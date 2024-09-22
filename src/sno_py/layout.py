import sys

from prompt_toolkit.application import get_app
from prompt_toolkit.filters import Condition, has_focus
from prompt_toolkit.layout import (ConditionalContainer, Float, FloatContainer,
                                   HSplit, Layout, VSplit, Window)
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.margins import ConditionalMargin, NumberedMargin
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import (BeforeInput,
                                              HighlightSearchProcessor,
                                              HighlightSelectionProcessor,
                                              ShowTrailingWhiteSpaceProcessor,
                                              TabsProcessor)
from prompt_toolkit.lexers import DynamicLexer, PygmentsLexer
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar, SearchToolbar

from sno_py.vi_modes import get_input_mode


class CommandToolBar(ConditionalContainer):
    def __init__(self, editor) -> None:
        super(CommandToolBar, self).__init__(
            Window(
                BufferControl(
                    buffer=editor.command_buffer,
                    input_processors=[BeforeInput(":")],
                ),
                height=1
            ),
            filter=has_focus(editor.command_buffer)
        )


class LogToolBar(ConditionalContainer):
    def __init__(self, editor) -> None:
        super(LogToolBar, self).__init__(
            Window(
                BufferControl(
                    buffer=editor.log_buffer
                ),
                height=1
            ),
            filter=has_focus(editor.log_buffer)
        )


class SnoLayout:
    def __init__(self, editor) -> None:
        self.editor = editor
        self.search_toolbar = SearchToolbar(
            vi_mode=True, search_buffer=editor.search_buffer)
        self.search_control = self.search_toolbar.control

    @property
    def layout(self):
        return Layout(
            FloatContainer(
                content=HSplit([
                    Window(
                        BufferControl(
                            lexer=PygmentsLexer.from_filename(
                                    self.editor.active_buffer.display_name),
                            include_default_input_processors=False,
                            input_processors=[
                                ShowTrailingWhiteSpaceProcessor(),
                                HighlightSelectionProcessor(),
                                HighlightSearchProcessor(),
                                TabsProcessor(
                                    tabstop=self.editor.tabstop,
                                    char1=(
                                        lambda: '|' if self.editor.display_unprintable_characters else ' '),
                                    char2=(lambda: _try_char('\u2508', '.', get_app().output.encoding())
                                           if self.editor.display_unprintable_characters else ' '),
                                )
                            ],
                            buffer=self.editor.active_buffer.buffer_inst,
                            search_buffer_control=self.search_control,
                            focus_on_click=True,
                            preview_search=True),
                        left_margins=[
                            ConditionalMargin(
                                margin=NumberedMargin(
                                    display_tildes=True,
                                    relative=Condition(lambda: self.editor.show_relative_numbers)),
                                filter=Condition(
                                    lambda: self.editor.show_line_numbers)
                            )],
                        style="class:background"
                    ),
                    VSplit(
                        [
                            FormattedTextToolbar(lambda: str(
                                get_input_mode()), style="class:pygments.string class:container"),
                        ],
                        width=Dimension()
                    ),
                    LogToolBar(self.editor),
                    self.search_toolbar,
                    CommandToolBar(self.editor)
                ]), floats=[
                    Float(
                        xcursor=True,
                        ycursor=True,
                        content=CompletionsMenu(
                            max_height=16, scroll_offset=1),
                    )
                ]))


def _try_char(character: str, backup, encoding=sys.stdout.encoding):
    """
    Return `character` if it can be encoded using sys.stdout, else return the
    backup character.
    """
    if character.encode(encoding, 'replace') == b'?':
        return backup
    else:
        return character
