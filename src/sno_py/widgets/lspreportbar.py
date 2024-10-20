from functools import cached_property
from typing import Optional, TYPE_CHECKING

from prompt_toolkit.layout import ConditionalContainer
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar
from prompt_toolkit.filters import Condition

from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.window import WindowManager
    from sansio_lsp_client import Range


class _LspReportedBar(ConditionalContainer):
    """
    A conditional container for displaying messages reported by the LSP.

    Attributes:
        wm (Optional[WindowManager]): The window manager accessing current editor windows and buffers.
    """

    def __init__(self) -> None:
        """Initialize the _LspReportedBar with conditions to fetch and style messages."""
        self.wm: Optional["WindowManager"] = None

        def get_message_at_cursor() -> Optional[str]:
            """Retrieve the LSP message at the current cursor position.

            Returns:
                Optional[str]: The LSP message, or an empty string if none is found.
            """
            if self.wm is None:
                self.wm = container["WindowManager"]
            active_buffer = self.wm.active_window.active_buffer
            if active_buffer is None:
                return ""
            line = active_buffer.buffer.document.cursor_position_row
            for report in active_buffer.lsp_reports:
                message: str = report["message"]
                rrange: "Range" = report["range"]
                if rrange.start.line == line:
                    return message

        def get_style_at_cursor() -> str:
            """Retrieve the style class based on the current cursor position.

            Returns:
                str: Style class for LSP error or warning.
            """
            if self.wm is None:
                self.wm = container["WindowManager"]
            active_buffer = self.wm.active_window.active_buffer
            if active_buffer is None:
                return ""
            line = active_buffer.buffer.document.cursor_position_row
            for report in active_buffer.lsp_reports:
                rrange: "Range" = report["range"]
                if rrange.start.line == line:
                    return (
                        "class:lsp.error" if report["is_error"] else "class:lsp.warning"
                    )

        super(_LspReportedBar, self).__init__(
            FormattedTextToolbar(
                get_message_at_cursor,
                style=get_style_at_cursor,
            ),
            filter=Condition(lambda: bool(get_message_at_cursor())),
        )


class LspReporterBar:
    """Interface for creating an LSP reporter bar."""

    def __init__(self) -> None:
        """Initialize the LspReporterBar."""
        pass

    @cached_property
    def container(self) -> ConditionalContainer:
        """Retrieve the conditional container for the LSP reporter bar.

        Returns:
            ConditionalContainer: The LSP reporter bar component.
        """
        return _LspReportedBar()
