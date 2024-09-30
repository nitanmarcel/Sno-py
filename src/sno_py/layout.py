import asyncio
import os
import sys
from typing import Callable, Iterable, Optional

import anyio
import ptvertmenu
from prompt_toolkit.application import get_app
from prompt_toolkit.filters import Condition, has_focus, is_searching
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (ConditionalContainer, Float, FloatContainer,
                                   HSplit, Layout, VSplit, Window, WindowAlign)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.margins import ConditionalMargin, NumberedMargin
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import (BeforeInput,
                                              HighlightSearchProcessor,
                                              HighlightSelectionProcessor,
                                              Processor,
                                              ShowTrailingWhiteSpaceProcessor,
                                              TabsProcessor, Transformation,
                                              TransformationInput)
from prompt_toolkit.layout.utils import explode_text_fragments
from prompt_toolkit.lexers import DynamicLexer, PygmentsLexer
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar, SearchToolbar

from sno_py.vi_modes import get_input_mode


class TreeItem:
    def __init__(self, name, path, is_dir, is_root=False):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.children = []
        self.expanded = is_root
        self.is_root = is_root


class TreeDirectoryMenu(ConditionalContainer):
    def __init__(self, editor) -> None:
        self.editor = editor
        self.root = self.build_tree(".", is_root=True)
        self.menu_items = self.get_menu_items()

        self.menu = ptvertmenu.VertMenu(
            items=self.menu_items, accept_handler=self.accept_handler
        )

        super().__init__(self.menu, filter=editor.filters.tree_menu_toggled)

    def build_tree(self, path, is_root=False):
        root = TreeItem(os.path.basename(path), path, True, is_root)
        for item in sorted(os.listdir(path)):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                root.children.append(self.build_tree(full_path))
            else:
                root.children.append(TreeItem(item, full_path, False))
        return root

    def get_menu_items(self, node=None, level=0):
        if node is None:
            node = self.root

        items = []
        prefix = "  " * level
        if node.is_dir:
            if node.is_root:
                # For root, always show as expanded and don't include in the menu
                for child in node.children:
                    items.extend(self.get_menu_items(child, level))
            else:
                icon = "▼" if node.expanded else "▶"
                items.append((f"{prefix}{icon} {node.name}", node.path))
                if node.expanded:
                    for child in node.children:
                        items.extend(self.get_menu_items(child, level + 1))
        else:
            items.append((f"{prefix}{node.name}", node.path))
        return items

    def accept_handler(self, item):
        path = item[1]
        if os.path.isdir(path):
            self.toggle_directory(path)
        else:
            asyncio.create_task(self.editor.create_file_buffer(path))
            self.editor.close_tree_menu()

    def toggle_directory(self, dir_path):
        node = self.find_node(self.root, dir_path)
        if node and not node.is_root:
            node.expanded = not node.expanded
            self.menu_items = self.get_menu_items()
            self.menu.items = self.menu_items

            toggled_index = next(
                (i for i, item in enumerate(self.menu_items) if item[1] == dir_path),
                None,
            )
            if toggled_index is not None:
                self.menu.selected_item = self.menu_items[toggled_index]

    def find_node(self, node, path):
        if node.path == path:
            return node
        if node.is_dir:
            for child in node.children:
                found = self.find_node(child, path)
                if found:
                    return found
        return None


class StatusBar(FormattedTextToolbar):
    def __init__(self, editor) -> None:
        super(StatusBar, self).__init__(
            get_input_mode, style="class:pygments.string class:container"
        )


class StatusBarRuller(Window):
    def __init__(self, editor) -> None:
        super(StatusBarRuller, self).__init__(
            FormattedTextControl(
                lambda: f" {editor.active_buffer.display_name}"
                + ("* | " if not editor.active_buffer.saved else " | ")
                + f"{editor.filetype.guess_filetype(editor.active_buffer._path, editor.active_buffer.buffer_inst.document.text)} "
                f"- {editor.active_buffer.buffer_inst.document.cursor_position_row + 1},"
                f"{editor.active_buffer.buffer_inst.document.cursor_position_col + 1}"
                " "
            ),
            align=WindowAlign.RIGHT,
            style="class:pygments.string class:container",
            height=1,
        )


class CommandToolBar(ConditionalContainer):
    def __init__(self, editor) -> None:
        super(CommandToolBar, self).__init__(
            Window(
                BufferControl(
                    buffer=editor.command_buffer,
                    input_processors=[BeforeInput(":")],
                ),
                height=1,
            ),
            filter=has_focus(editor.command_buffer),
        )


class LogToolBar(ConditionalContainer):
    def __init__(self, editor) -> None:
        super(LogToolBar, self).__init__(
            Window(BufferControl(buffer=editor.log_buffer), height=1),
            filter=has_focus(editor.log_buffer),
        )


class LspReporterToolBar(ConditionalContainer):
    def __init__(self, editor) -> None:
        def get_message_at_cursor():
            if (active_buffer := editor.active_buffer) is not None:
                line = active_buffer.buffer_inst.document.cursor_position_row
                for report in active_buffer.reports():
                    if report.range.start.line == line:
                        return report.message
            return []

        super(LspReporterToolBar, self).__init__(
            FormattedTextToolbar(get_message_at_cursor, style="class:lsp-message-text"),
            filter=~has_focus(editor.command_buffer)
            & ~is_searching
            & ~has_focus("system")
            & Condition(get_message_at_cursor),
        )


class LspReporterProcessor(Processor):
    def __init__(self, editor) -> None:
        self._editor = editor

    def apply_transformation(
        self, transformation_input: TransformationInput
    ) -> Transformation:
        fragments = transformation_input.fragments
        if (active_buffer := self._editor.active_buffer) is not None:
            for report in active_buffer.reports():
                if report.range.start.line == transformation_input.lineno:
                    fragments = explode_text_fragments(fragments)
                    for i in range(
                        report.range.start.character, report.range.end.character
                    ):
                        if i < len(fragments):
                            fragments[i] = (" class:pygments.error", fragments[i][1])
        return Transformation(fragments)


class SnoLayout:
    def __init__(self, editor) -> None:
        self.editor = editor
        self.search_toolbar = SearchToolbar(
            vi_mode=True, search_buffer=editor.search_buffer
        )
        self.search_control = self.search_toolbar.control
        self.status_bar = VSplit([StatusBar(self.editor), StatusBarRuller(self.editor)])
        self.directory_tree = TreeDirectoryMenu(self.editor)

    @property
    def layout(self):
        fc = FloatContainer(
            content=VSplit(
                [
                    self.directory_tree,
                    Window(
                        BufferControl(
                            buffer=self.editor.active_buffer.buffer_inst,
                            search_buffer_control=self.search_control,
                            focus_on_click=True,
                            preview_search=True,
                            lexer=PygmentsLexer.from_filename(
                                self.editor.active_buffer.display_name,
                                sync_from_start=False,
                            ),
                            include_default_input_processors=False,
                            input_processors=[
                                LspReporterProcessor(self.editor),
                                ShowTrailingWhiteSpaceProcessor(),
                                HighlightSelectionProcessor(),
                                HighlightSearchProcessor(),
                                TabsProcessor(
                                    tabstop=self.editor.tabstop,
                                    char1=(
                                        lambda: (
                                            "|"
                                            if self.editor.display_unprintable_characters
                                            else " "
                                        )
                                    ),
                                    char2=(
                                        lambda: (
                                            _try_char(
                                                "\u2508",
                                                ".",
                                                get_app().output.encoding(),
                                            )
                                            if self.editor.display_unprintable_characters
                                            else " "
                                        )
                                    ),
                                ),
                            ],
                        ),
                        left_margins=[
                            ConditionalMargin(
                                margin=NumberedMargin(
                                    display_tildes=True,
                                    relative=Condition(
                                        lambda: self.editor.show_relative_numbers
                                    ),
                                ),
                                filter=Condition(lambda: self.editor.show_line_numbers),
                            )
                        ],
                    ),
                ]
            ),
            floats=[
                Float(
                    xcursor=True,
                    ycursor=True,
                    content=CompletionsMenu(
                        max_height=12,
                        scroll_offset=2,
                        extra_filter=~has_focus(self.editor.command_buffer),
                    ),
                )
            ],
        )

        layout = Layout(
            HSplit(
                [
                    fc,
                    self.status_bar,
                    CommandToolBar(self.editor),
                    LspReporterToolBar(self.editor),
                    LogToolBar(self.editor),
                    self.search_toolbar,
                ],
                style="class:background",
            ),
            focused_element=self.editor.active_buffer.buffer_inst,
        )
        return layout


def _try_char(character: str, backup, encoding=sys.stdout.encoding):
    """
    Return `character` if it can be encoded using sys.stdout, else return the
    backup character.
    """
    if character.encode(encoding, "replace") == b"?":
        return backup
    else:
        return character
