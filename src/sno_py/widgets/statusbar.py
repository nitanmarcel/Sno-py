from functools import cached_property
from typing import TYPE_CHECKING, Callable, Union

from prompt_toolkit.application import get_app
from prompt_toolkit.layout import VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.selection import SelectionType

from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.editor import Editor


class _StatusBar(FormattedTextToolbar):
    """A status bar component displaying text with a consistent style.

    Attributes:
        id (str): The unique identifier for the status bar.
    """

    def __init__(self, text: Union[str, Callable[..., str]]) -> None:
        """Initialize the status bar with specified text.

        Args:
            text (str | Callable[..., str]): The text or callable that provides text for the status bar.
        """
        self.id = "status_bar"
        super(_StatusBar, self).__init__(text, style="class:statusbar")


class _StatusBarRuller(Window):
    """A status bar component, aligned to the right.

    Attributes:
        id (str): The unique identifier for the status bar ruler.
    """

    def __init__(self, text: Union[str, Callable[..., str]]) -> None:
        """Initialize the status bar ruler with specified text.

        Args:
            text (str | Callable[..., str]): The text or callable that provides text for the status bar ruler.
        """
        self.id = "status_bar_ruller"
        super(_StatusBarRuller, self).__init__(
            FormattedTextControl(text),
            align=WindowAlign.RIGHT,
            style="class:statusbar",
            height=1,
        )

    def focus(self) -> None:
        """Do nothing when focus is called, as this is non-interactive."""
        pass


class _StatusBarVSplit(VSplit):
    """A vertical split container for combining status bar components.

    Attributes:
        id (str): The unique identifier for the status bar split.
    """

    def __init__(
        self,
        ltext: Union[str, Callable[..., str]],
        rtext: Union[str, Callable[..., str]],
    ) -> None:
        """Initialize the status bar split with left and right text components.

        Args:
            ltext (str | Callable[..., str]): The text or callable for the left status bar component.
            rtext (str | Callable[..., str]): The text or callable for the right status bar ruler.
        """
        self.id = "status_bar"
        super(_StatusBarVSplit, self).__init__(
            [_StatusBar(ltext), _StatusBarRuller(rtext)]
        )

    def focus(self) -> None:
        """Do nothing when focus is called, as this is non-interactive."""
        pass

    @property
    def focused(self) -> bool:
        """Always returns False as there is no focus for the status bar split.

        Returns:
            bool: False
        """
        return False


class StatusBar:
    """Encapsulates the components necessary for displaying a status bar in an editor."""

    def __init__(self) -> None:
        """Initialize the StatusBar with input mode and cursor position text sources."""
        self.ltext: Union[str, Callable[..., str]] = self._get_input_mode
        self.rtext: Union[str, Callable[..., str]] = self._get_cursor_pos_text
        self.editor: "Editor" = container["Editor"]

    @cached_property
    def container(self) -> VSplit:
        """Retrieve the container for the status bar components.

        Returns:
            VSplit: The vertical split containing status bar components.
        """
        return _StatusBarVSplit(self.ltext, self.rtext)

    def _get_input_mode(self) -> str:
        """Fetch the current input mode of the editor for display.

        Returns:
            str: A string representation of the current input mode.
        """
        input_mode: InputMode = get_app().vi_state.input_mode

        vi_mode: str = "-- ? --"
        match input_mode:
            case InputMode.INSERT:
                vi_mode = "-- INSERT --"
            case InputMode.INSERT_MULTIPLE:
                vi_mode = "-- INSERT --"
            case InputMode.REPLACE:
                vi_mode = "-- REPLACE --"
            case InputMode.REPLACE_SINGLE:
                vi_mode = "-- REPLACE SINGLE --"
            case InputMode.NAVIGATION:
                vi_mode = "-- NORMAL --"
            case _:
                vi_mode = "-- ? --"
        if (state := get_app().current_buffer.selection_state) is not None:
            match state.type:
                case SelectionType.LINES:
                    vi_mode = "-- VISUAL LINE --"
                case SelectionType.BLOCK:
                    vi_mode = "-- VISUAL BLOCK --"
                case SelectionType.CHARACTERS:
                    vi_mode = "-- VISUAL --"
                case _:
                    return vi_mode
        return vi_mode

    def _get_cursor_pos_text(self) -> str:
        """Fetch the current position of the cursor along with buffer status for display.

        Returns:
            str: A formatted string with the buffer name and the cursor's current position.
        """
        if self.editor.wm.active_window and self.editor.wm.active_window.active_buffer:
            buffer = self.editor.wm.active_window.active_buffer
            return (
                f" {buffer.get_display_name()}"
                + ("*" if buffer.changed else "")
                + f" | {buffer.buffer.document.cursor_position_row + 1},"
                f"{buffer.buffer.document.cursor_position_col + 1}"
            )
        return ""
