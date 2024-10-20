from typing import TYPE_CHECKING, Any, Callable, Union

from prompt_toolkit.layout import ConditionalContainer, HSplit, Window
from prompt_toolkit.filters import Always
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.widgets import HorizontalLine

from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.window import EditorWindow, WindowManager


class _TabControl(FormattedTextControl):
    """Control for rendering and managing the tab bar of editor windows.

    Attributes:
        pwindow (EditorWindow | None): The parent editor window of this tab control.
        wm (WindowManager): The window manager controlling the editor windows.
    """

    def __init__(self, wm: "WindowManager") -> None:
        """Initialize the tab control with a given window manager.

        Args:
            wm (WindowManager): The window manager to be used for managing tabs.
        """
        self.pwindow: Union["EditorWindow", None] = None
        self.wm: "WindowManager" = wm
        super(_TabControl, self).__init__(self._get_tokens, style="class:container")

    def _set_pwindow(self) -> None:
        """Set the parent window for this tab control by traversing the window hierarchy."""

        def walk_and_find(elem: Any) -> bool:
            if elem is self:
                return True
            if hasattr(elem, "content"):
                return walk_and_find(elem.content)
            if hasattr(elem, "children"):
                for child in elem.children:
                    if walk_and_find(child):
                        return True
            return False

        if self.pwindow is None:
            for win in self.wm.walk_windows():
                for bar in win.walk_top_bars():
                    if walk_and_find(bar):
                        self.pwindow = win

    def tab_handler(self, index: int) -> Callable[..., None]:
        """Create a handler for tab selection events.

        Args:
            index (int): The index of the tab to be handled.

        Returns:
            Callable[..., None]: A function that handles mouse events for tab selection.
        """
        self._set_pwindow()

        def handler(e: MouseEvent) -> None:
            if e.event_type == MouseEventType.MOUSE_DOWN:
                self.pwindow.select_buffer_by_index(index)

        return handler

    def _get_tokens(self) -> list:
        """Generate the token list for rendering the tab control.

        Returns:
            list: A list of tokens used for rendering the tab control.
        """
        self._set_pwindow()
        result: list = []
        selected_index: int = self.pwindow.get_active_buffer_index()
        for i, buff in enumerate(self.pwindow.buffers):
            text: str = buff.get_display_name()
            if buff.changed:
                text += "*"
            if i == selected_index:
                result.append(
                    ("class:selection underline", f" {text} ", self.tab_handler(i))
                )
            else:
                result.append(("class:container", f" {text} ", self.tab_handler(i)))
            result.append(("class:container", " "))
        return result


class _TabBar(ConditionalContainer):
    """A container for managing and displaying a tab bar with a horizontal line divider.

    Attributes:
        id (str): The unique identifier for the tab bar.
        pwindow (EditorWindow | None): The parent editor window of this tab bar.
        wm (WindowManager): The window manager controlling the editor windows.
    """

    def __init__(self) -> None:
        """Initialize the tab bar using the window manager."""
        self.id: str = "tab_bar"
        self.pwindow: Union["EditorWindow", None] = None
        self.wm: "WindowManager" = container["WindowManager"]
        super(_TabBar, self).__init__(
            HSplit([Window(_TabControl(self.wm), height=1), HorizontalLine()]),
            filter=Always(),
        )


class TabBar:
    """A public interface for creating a tab bar in the editor."""

    def __init__(self) -> None:
        """Initialize the TabBar."""
        pass

    @property
    def container(self) -> _TabBar:
        """Get the tab bar container.

        Returns:
            _TabBar: The container representing the tab bar.
        """
        return _TabBar()
