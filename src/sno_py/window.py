from typing import TYPE_CHECKING, Generator, List, Optional, Union

from prompt_toolkit.application import get_app
from prompt_toolkit.layout import (
    Container,
    Float,
    FloatContainer,
    HSplit,
    Layout,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import Processor
from prompt_toolkit.widgets import HorizontalLine, VerticalLine

from sno_py.di import container

if TYPE_CHECKING:
    from prompt_toolkit.layout import SearchBufferControl
    from sno_py.editor import Editor
    from sno_py.buffer import EditorBuffer
    from sno_py.storage.bars import BarsStorage


class EditorWindow:
    """A window in the editor that manages multiple editor buffers.

    Attributes:
        buffers (List[EditorBuffer]): List of all buffers in this window.
        active_buffer (EditorBuffer): The currently active buffer in the window.
        input_processors (List[Processor]): Processors for handling input transformations.
        searchbuffer_control (Optional[SearchBufferControl]): Control for search operations within the buffer.
        buffer_control (BufferControl): Control managing buffer display and behavior.
        window (Window): The graphical component representing the window.
        created_top_bars (List[Container]): Top bars added to this window.
        created_bottom_bars (List[Container]): Bottom bars added to this window.
        editor (Editor): Reference to the parent editor.
    """

    def __init__(self, editor_buffer: "EditorBuffer") -> None:
        """Initialize an editor window with a specified buffer.

        Args:
            editor_buffer (EditorBuffer): The initial buffer to be loaded into the window.
        """
        self.buffers: List["EditorBuffer"] = [editor_buffer]
        self.active_buffer: "EditorBuffer" = editor_buffer
        self.input_processors: List["Processor"] = container[
            "ProcessorsStorage"
        ].get_processors()
        self.searchbuffer_control: Optional["SearchBufferControl"] = None
        self.buffer_control: BufferControl = BufferControl(
            buffer=self.active_buffer.buffer,
            search_buffer_control=lambda: self.searchbuffer_control,
            lexer=self.active_buffer.lexer,
            preview_search=True,
            input_processors=self.input_processors,
            include_default_input_processors=False,
        )
        self.window: Window = Window(self.buffer_control, style="class:background")

        self._bars_store: "BarsStorage" = container["BarsStorage"]
        self.created_top_bars: List[Container] = [
            b.container for b in self._bars_store.get_top_bars()
        ]
        self.created_bottom_bars: List[Container] = [
            b.container for b in self._bars_store.get_bottom_bars()
        ]

        self.editor: "Editor" = container["Editor"]

    def create_container(self) -> Container:
        """Create and return the container layout for this window.

        Returns:
            Container: The container object representing the window layout.
        """
        for bar in self.created_bottom_bars:
            if getattr(bar, "id", None) == "search_bar":
                self.searchbuffer_control = getattr(bar, "search_control", None)
        return HSplit([*self.created_top_bars, self.window, *self.created_bottom_bars])

    def add_buffer(self, buffer: "EditorBuffer") -> None:
        """Add a new buffer to this window.

        Args:
            buffer (EditorBuffer): The buffer to add.
        """
        self.buffers.append(buffer)

    def switch_to_buffer(self, buffer: "EditorBuffer") -> None:
        """Switch to a specified buffer if it exists in this window.

        Args:
            buffer (EditorBuffer): The buffer to switch to.
        """
        if buffer in self.buffers:
            self.active_buffer = buffer
            self.buffer_control.buffer = self.active_buffer.buffer

    def select_buffer_by_name(
        self, name: str, short: bool = True
    ) -> Optional["EditorBuffer"]:
        """Select a buffer by its name and return it if found.

        Args:
            name (str): The name of the buffer to select.
            short (bool, optional): Use short name for buffer. Defaults to True.

        Returns:
            Optional[EditorBuffer]: The selected buffer if found, otherwise None.
        """
        for buffer in self.buffers:
            if buffer.get_display_name(short) == name:
                self.switch_to_buffer(buffer)
                return buffer
        return None

    def select_buffer_by_index(self, index: int) -> Optional["EditorBuffer"]:
        """Select a buffer by its index and return it if found.

        Args:
            index (int): The index of the buffer to select.

        Returns:
            Optional[EditorBuffer]: The selected buffer if found, otherwise None.
        """
        if 0 <= index < len(self.buffers):
            buffer = self.buffers[index]
            self.switch_to_buffer(buffer)
            return buffer
        return None

    def get_active_buffer_index(self) -> int:
        """Get the index of the active buffer.

        Returns:
            int: The index of the current active buffer.
        """
        return self.buffers.index(self.active_buffer)

    def get_buffer_count(self) -> int:
        """Get the total number of buffers in this window.

        Returns:
            int: Total buffer count.
        """
        return len(self.buffers)

    def walk_buffers(self) -> Generator["EditorBuffer", None, None]:
        """Generator to iterate over all buffers in this window.

        Yields:
            Generator[EditorBuffer, None, None]: An iterator over buffers.
        """
        yield from self.buffers

    def walk_top_bars(self, created: bool = True) -> Generator[Container, None, None]:
        """Generator to iterate over top bars in this window.

        Args:
            created (bool, optional): Use created top bars. Defaults to True.

        Yields:
            Generator[Container, None, None]: An iterator over top bar containers.
        """
        yield from self.created_top_bars if created else self.top_bars

    def walk_bottom_bars(
        self, created: bool = True
    ) -> Generator[Container, None, None]:
        """Generator to iterate over bottom bars in this window.

        Args:
            created (bool, optional): Use created bottom bars. Defaults to True.

        Yields:
            Generator[Container, None, None]: An iterator over bottom bar containers.
        """
        yield from self.created_bottom_bars if created else self.bottom_bars


class SplitContainer:
    """A container that can be split horizontally or vertically.

    Attributes:
        children (List[Union[SplitContainer, EditorWindow]]): Child containers or windows.
        is_horizontal (bool): Orientation of the split (horizontal or vertical).
    """

    def __init__(
        self,
        children: List[Union["SplitContainer", EditorWindow]],
        is_horizontal: bool = True,
    ) -> None:
        """Initialize a SplitContainer with given children and orientation.

        Args:
            children (List[Union[SplitContainer, EditorWindow]]): Child containers or windows.
            is_horizontal (bool, optional): Whether to split horizontally. Defaults to True.
        """
        self.children: List[Union["SplitContainer", EditorWindow]] = children
        self.is_horizontal: bool = is_horizontal

    def create_container(self) -> Container:
        """Create and return the container layout with splits.

        Returns:
            Container: The container object with splits.
        """
        split_class = HSplit if self.is_horizontal else VSplit
        separator_class = HorizontalLine if self.is_horizontal else VerticalLine

        components = []
        for i, child in enumerate(self.children):
            if i > 0:
                components.append(separator_class())
            components.append(child.create_container())
        return split_class(components)


class WindowManager:
    """Manages the layout and windows of the editor.

    Attributes:
        _layout (Optional[Layout]): The current prompt_toolkit layout.
        root (Optional[SplitContainer]): The root container of the layout.
        active_window (Optional[EditorWindow]): The currently active window.
        default_containers (List[Container]): Default containers in the layout.
        global_top_bars (List[Container]): Global top bars available to all windows.
        global_bottom_bars (List[Container]): Global bottom bars available to all windows.
        floats (List[Float]): Floating elements in the layout.
    """

    def __init__(self) -> None:
        """Initialize the WindowManager with default configuration."""
        self._layout: Optional[Layout] = None
        self.root: Optional[SplitContainer] = None
        self.active_window: Optional[EditorWindow] = None
        self.default_containers: List[Container] = []
        self.global_top_bars: List[Container] = []
        self.global_bottom_bars: List[Container] = []
        self.floats: List[Float] = [
            Float(
                content=CompletionsMenu(max_height=12, scroll_offset=2),
                xcursor=True,
                ycursor=True,
            )
        ]

    async def create_buffer(
        self, location: str, content: str = "", cursor_pos: int = 0
    ) -> "EditorBuffer":
        """Create and return a new EditorBuffer.

        Args:
            location (str): The file location for the buffer.
            content (str, optional): Initial content of the buffer. Defaults to "".
            cursor_pos (int, optional): Initial cursor position. Defaults to 0.

        Returns:
            EditorBuffer: The newly created editor buffer.
        """
        buffer: "EditorBuffer" = container["EditorBuffer"](location, content)
        await buffer.read()
        buffer.buffer.cursor_position = (
            buffer.buffer.document.translate_row_col_to_index(cursor_pos, 0)
        )
        return buffer

    def create_window(self, buffer: "EditorBuffer") -> EditorWindow:
        """Create and return a new EditorWindow.

        Args:
            buffer (EditorBuffer): The buffer to associate with the new window.

        Returns:
            EditorWindow: The newly created editor window.
        """
        window: EditorWindow = EditorWindow(buffer)
        window.top_bars = self.global_top_bars.copy()
        window.bottom_bars = self.global_bottom_bars.copy()
        if self.active_window is not None:
            window.created_top_bars = self.active_window.created_top_bars.copy()
            window.created_bottom_bars = self.active_window.created_bottom_bars.copy()
        self.focus_window(window)
        return window

    def _update_layout(self) -> None:
        """Internal method to update the layout."""
        active_window = self.active_window
        new_layout = self.create_layout()
        get_app().layout.container = new_layout.container
        if active_window:
            get_app().layout.focus(active_window.window)

    def set_layout(self, root: SplitContainer) -> None:
        """Set the root layout of the window manager.

        Args:
            root (SplitContainer): Root container for the layout.
        """
        self.root = root

    def add_default_container(self, container: Container) -> None:
        """Add a default container to the layout.

        Args:
            container (Container): The container to be added as default.
        """
        self.default_containers.append(container)

    def get_bar_by_id(self, id: str) -> Optional[Container]:
        """Get a bar by its ID.

        Args:
            id (str): The ID of the bar to find.

        Returns:
            Optional[Container]: The container with the matching ID, if found.
        """
        if self.active_window:
            for bar in (
                self.active_window.created_top_bars
                + self.active_window.created_bottom_bars
            ):
                if getattr(bar, "id", None) == id:
                    return bar
        return None

    def _get_all_windows(
        self, container: Optional[Union[SplitContainer, EditorWindow]]
    ) -> List[EditorWindow]:
        """Get all windows in the layout.

        Args:
            container (Optional[Union[SplitContainer, EditorWindow]]): The starting container for window search.

        Returns:
            List[EditorWindow]: All editor windows within the container.
        """
        if container is None:
            return []
        if isinstance(container, EditorWindow):
            return [container]
        return [
            window
            for child in container.children
            for window in self._get_all_windows(child)
        ]

    def create_layout(self) -> Layout:
        """Create and return the layout for the editor.

        Returns:
            Layout: The prompt_toolkit layout containing all elements.
        """
        if self.root is None:
            content = HSplit(self.default_containers)
        else:
            main_container: Container = self.root.create_container()
            content = HSplit([*self.default_containers, main_container])

        float_container = FloatContainer(
            content=content, floats=self.floats, style="class:background"
        )

        self._layout = Layout(float_container)
        return self._layout

    async def split(
        self,
        window: EditorWindow | None = None,
        is_horizontal: bool = True,
        new_buffer: Optional["EditorBuffer"] = None,
    ) -> None:
        """Split a given window and add a new buffer to the layout.

        Args:
            window (EditorWindow | None, optional): The window to split. Defaults to currently active window.
            is_horizontal (bool, optional): Whether to split horizontally. Defaults to True.
            new_buffer (Optional[EditorBuffer], optional): The new buffer to include. Defaults to the buffer of window being split.
        """
        if window is None:
            window = self.active_window
        if new_buffer is None:
            new_buffer = window.active_buffer
        new_window: EditorWindow = self.create_window(new_buffer)

        if self.root is None:
            self.root = SplitContainer(
                [window, new_window], is_horizontal=is_horizontal
            )
        else:
            parent = self._find_parent(self.root, window)
            if parent is None:
                self.root = SplitContainer(
                    [self.root, new_window], is_horizontal=is_horizontal
                )
            else:
                index = parent.children.index(window)
                if parent.is_horizontal == is_horizontal:
                    parent.children.insert(index + 1, new_window)
                else:
                    new_container = SplitContainer(
                        [window, new_window], is_horizontal=is_horizontal
                    )
                    parent.children[index] = new_container

        self.active_window = new_window
        try:
            self._update_layout()
        except ValueError:
            pass

    def _find_topmost_parent(
        self, container: Union[SplitContainer, EditorWindow], window: EditorWindow
    ) -> Optional[SplitContainer]:
        """Find the topmost parent container of a window.

        Args:
            container (Union[SplitContainer, EditorWindow]): The starting container for parent search.
            window (EditorWindow): The window whose parent is sought.

        Returns:
            Optional[SplitContainer]: The topmost parent SplitContainer, if found.
        """
        if isinstance(container, EditorWindow):
            return None
        for child in container.children:
            if child == window:
                return container
            if isinstance(child, SplitContainer):
                result = self._find_topmost_parent(child, window)
                if result:
                    return container
        return None

    def _find_parent(
        self, container: Union[SplitContainer, EditorWindow], window: EditorWindow
    ) -> Optional[SplitContainer]:
        """Find the immediate parent container of a window.

        Args:
            container (Union[SplitContainer, EditorWindow]): The starting container for parent search.
            window (EditorWindow): The window whose parent is sought.

        Returns:
            Optional[SplitContainer]: The immediate parent SplitContainer, if found.
        """
        if isinstance(container, EditorWindow):
            return None
        for child in container.children:
            if child == window:
                return container
            if isinstance(child, SplitContainer):
                result = self._find_parent(child, window)
                if result:
                    return result
        return None

    async def close_window(self, window: EditorWindow) -> None:
        """Close the specified window and update the layout.

        Args:
            window (EditorWindow): The window to close.
        """
        if self.root == window:
            self.root = None
            self.active_window = None
        else:
            parent = self._find_parent(self.root, window)
            if parent:
                parent.children.remove(window)
                if len(parent.children) == 1:
                    grandparent = self._find_parent(self.root, parent)
                    if grandparent:
                        index = grandparent.children.index(parent)
                        grandparent.children[index] = parent.children[0]
                    else:
                        self.root = parent.children[0]

        if self.active_window == window:
            self.active_window = self._find_next_window(self.root)
        self._update_layout()

    def _find_next_window(
        self, container: Union[SplitContainer, EditorWindow]
    ) -> Optional[EditorWindow]:
        """Find the next available window in the layout.

        Args:
            container (Union[SplitContainer, EditorWindow]): The container to search within.

        Returns:
            Optional[EditorWindow]: The next EditorWindow found.
        """
        if isinstance(container, EditorWindow):
            return container
        for child in container.children:
            result = self._find_next_window(child)
            if result:
                return result
        return None

    def _get_window_list(self) -> List[EditorWindow]:
        """Get a list of all windows in the layout.

        Returns:
            List[EditorWindow]: An ordered list of all windows within the layout.
        """
        return self._get_all_windows(self.root)

    def focus_next_window(self) -> None:
        """Focus the next window in the layout."""
        windows = self._get_window_list()
        if not windows:
            return
        current_index = windows.index(self.active_window) if self.active_window else -1
        next_index = (current_index + 1) % len(windows)
        self.active_window = windows[next_index]
        get_app().layout.focus(self.active_window.window)

    def focus_previous_window(self) -> None:
        """Focus the previous window in the layout."""
        windows = self._get_window_list()
        if not windows:
            return
        current_index = windows.index(self.active_window) if self.active_window else 0
        prev_index = (current_index - 1) % len(windows)
        self.active_window = windows[prev_index]
        get_app().layout.focus(self.active_window.window)

    def focus_window(self, window: EditorWindow) -> None:
        """Focus the specified window.

        Args:
            window (EditorWindow): The window to be focused.
        """
        windows = self._get_window_list()
        if window in windows:
            self.active_window = window
            get_app().layout.focus(self.active_window.window)

    def walk_windows(self) -> Generator[EditorWindow, None, None]:
        """Generator to iterate over all windows in the layout.

        Yields:
            Generator[EditorWindow, None, None]: An iterator over editor windows.
        """
        yield from self._get_window_list()
