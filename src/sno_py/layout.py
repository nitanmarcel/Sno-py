import asyncio
import os
import sys
import ptvertmenu
from prompt_toolkit.application import get_app
from prompt_toolkit.filters import Condition, has_focus, is_searching
from prompt_toolkit.layout import (
    ConditionalContainer,
    Float,
    FloatContainer,
    HSplit,
    Layout,
    VSplit,
    Window,
    WindowAlign,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.margins import ConditionalMargin, NumberedMargin
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import (
    BeforeInput,
    HighlightSearchProcessor,
    HighlightSelectionProcessor,
    Processor,
    ShowTrailingWhiteSpaceProcessor,
    DisplayMultipleCursors,
    HighlightMatchingBracketProcessor,
    TabsProcessor,
    Transformation,
    TransformationInput,
)
from prompt_toolkit.layout.utils import explode_text_fragments
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar, SearchToolbar
from prompt_toolkit.keys import Keys
from prompt_toolkit.mouse_events import MouseEventType
from ptterm import Terminal

from sno_py.vi_modes import get_input_mode
from sno_py.fonts_utils import get_icon


class VSep(Window):
    def __init__(self):
        super(VSep, self).__init__(
            width=1, char="|", style="class:line class:pygments.Token"
        )


class HSep(Window):
    def __init__(self):
        super(HSep, self).__init__(
            height=1, char="-", style="class:line class:pygments.Token"
        )


class TreeItem:
    def __init__(self, name, path, is_dir, is_root=False):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.children = []
        self.expanded = is_root
        self.is_root = is_root
        self.loaded = False


class TreeDirectoryMenu(ConditionalContainer):
    def __init__(self, editor) -> None:
        self.editor = editor
        self.root = self.build_tree(".", is_root=True)
        self.menu_items = self.get_menu_items()

        self.menu = ptvertmenu.VertMenu(
            items=self.menu_items, accept_handler=self.accept_handler
        )

        super().__init__(
            VSplit([self.menu, VSep()]), filter=editor.filters.tree_menu_toggled
        )

    def build_tree(self, path, is_root=False):
        root = TreeItem(os.path.basename(path), path, True, is_root)
        if is_root:
            self.load_directory(root)
        return root

    def load_directory(self, node):
        if not node.loaded:
            for item in sorted(os.listdir(node.path)):
                full_path = os.path.join(node.path, item)
                if os.path.isdir(full_path):
                    node.children.append(TreeItem(item, full_path, True))
                else:
                    node.children.append(TreeItem(item, full_path, False))
            node.loaded = True

    def get_menu_items(self, node=None, level=0):
        if node is None:
            node = self.root

        items = []
        prefix = "  " * level
        if node.is_dir:
            if node.is_root:
                for child in node.children:
                    items.extend(self.get_menu_items(child, level))
            else:
                if self.editor.use_nerd_fonts:
                    icon = (
                        get_icon("oct-fold_down")
                        if node.expanded
                        else get_icon("oct-fold")
                    )
                else:
                    icon = "▼" if node.expanded else "▶"
                items.append((f"{prefix}{icon} {node.name}", node.path))
                if node.expanded and node.loaded:
                    for child in node.children:
                        items.extend(self.get_menu_items(child, level + 1))
        else:
            if self.editor.use_nerd_fonts:
                icon = self.editor.filetype.guess_filetype_icon(node.path)
                items.append((f"{prefix}{icon} {node.name}", node.path))
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
            if node.expanded and not node.loaded:
                self.load_directory(node)
            elif not node.expanded:
                node.children = []
                node.loaded = False
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


class TerminalSplit(ConditionalContainer):
    def __init__(self, editor):
        self.editor = editor
        self.terminal = Terminal(
            command=self.editor.terminal,
            height=Dimension(preferred=20),
            width=Dimension(),
            done_callback=self._on_done,
        )
        self.is_terminated = False
        self._is_close_requested = False
        super(TerminalSplit, self).__init__(
            HSplit([HSep(), self.terminal]), filter=self.editor.filters.terminal_toggled
        )

    def _on_done(self):
        if not self._is_close_requested:
            self.is_terminated = True
            self.editor.close_terminal()
            self.editor.refresh_layout()

    def kill_terminal(self):
        self._is_close_requested = True
        self.terminal.process.write_input("exit")
        self.terminal.process.write_key(Keys.Enter)


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


class TabControl(FormattedTextControl):
    def __init__(self, editor):
        self.editor = editor

        super(TabControl, self).__init__(self.get_tokens, style="class:container")

    def tab_handler(self, index):
        def handler(mouse_event):
            if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
                self.editor.select_buffer(index)

        return handler

    def get_tokens(self):
        selected_index = self.editor.active_buffer.index

        result = []

        for i, buffer in enumerate(self.editor.buffers):
            text = ""
            if self.editor.use_nerd_fonts:
                text = self.editor.filetype.guess_filetype_icon(buffer.path) + " "
            text += buffer.display_name
            if not buffer.saved:
                text = text + "*"
            handler = self.tab_handler(i)
            if i == selected_index:
                result.append(("class:selection underline", " %s " % text, handler))
            else:
                result.append(
                    ("class:pygments.Generic.Strong ", " %s " % text, handler)
                )
            result.append(("class:container", " "))
        return result


class TabToolBar(ConditionalContainer):
    def __init__(self, editor):
        super(TabToolBar, self).__init__(
            HSplit([Window(TabControl(editor), height=1), HSep()]),
            filter=Condition(lambda: len(editor.buffers) > 1),
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
    def __init__(self, editor):
        self.editor = editor
        self.search_toolbar = None
        self.search_control = None
        self.status_bar = None
        self.directory_tree = None
        self.terminal = None
        self.custom_hsplits = []
        self.custom_vsplits = []

    def add_hsplit(self, content):
        self.custom_hsplits.append(content)

    def add_vsplit(self, content):
        self.custom_vsplits.append(content)

    def _initialize_components(self):
        if not self.search_toolbar:
            self.search_toolbar = SearchToolbar(
                vi_mode=True, search_buffer=self.editor.search_buffer
            )
        if not self.search_control:
            self.search_control = self.search_toolbar.control
        if not self.status_bar:
            self.status_bar = VSplit(
                [StatusBar(self.editor), StatusBarRuller(self.editor)]
            )
        if not self.directory_tree:
            self.directory_tree = TreeDirectoryMenu(self.editor)
        if not self.terminal or self.terminal.is_terminated:
            self.terminal = TerminalSplit(self.editor)

    def _create_buffer_control(self):
        return BufferControl(
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
                HighlightMatchingBracketProcessor(),
                TabsProcessor(
                    tabstop=self.editor.tabstop,
                    char1=lambda: "|"
                    if self.editor.display_unprintable_characters
                    else " ",
                    char2=lambda: _try_char("\u2508", ".", get_app().output.encoding())
                    if self.editor.display_unprintable_characters
                    else " ",
                ),
                DisplayMultipleCursors(),
            ],
        )

    def _create_main_window(self):
        return Window(
            self._create_buffer_control(),
            left_margins=[
                ConditionalMargin(
                    margin=NumberedMargin(
                        display_tildes=True,
                        relative=Condition(lambda: self.editor.show_relative_numbers),
                    ),
                    filter=Condition(lambda: self.editor.show_line_numbers),
                )
            ],
        )

    @property
    def layout(self):
        self._initialize_components()

        main_vsplit = VSplit([self.directory_tree, self._create_main_window()])
        main_vsplit.children = main_vsplit.children + self.custom_vsplits

        main_hsplit = HSplit(
            [
                TabToolBar(self.editor),
                main_vsplit,
                self.terminal,
            ]
        )
        main_hsplit.children = main_hsplit.children + self.custom_hsplits

        fc = FloatContainer(
            content=main_hsplit,
            floats=[
                Float(
                    xcursor=True,
                    ycursor=True,
                    content=CompletionsMenu(max_height=12, scroll_offset=2),
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
