from typing import TYPE_CHECKING

from prompt_toolkit.application import Application
from prompt_toolkit.styles import DynamicStyle
from prompt_toolkit.clipboard.in_memory import InMemoryClipboard
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from prompt_toolkit.cursor_shapes import ModalCursorShapeConfig
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding.vi_state import InputMode

from sno_py.di import container

if TYPE_CHECKING:
    from argparse import Namespace
    from sno_py.bindings import EditorBindings
    from sno_py.buffer import EditorBuffer
    from sno_py.config import Config
    from sno_py.style import EditorStyle
    from sno_py.window import SplitContainer, WindowManager, EditorWindow


class Editor:
    """Main editor application managing the user interface and interaction.

    Attributes:
        app (Application | None): The prompt_toolkit application instance.
        config (Config): Application configuration settings.
        bindings (EditorBindings): Key binding configuration for the editor.
        wm (WindowManager): Window manager for managing editor panes.
        style (EditorStyle): Editor styling handler.
        _window_command_mode (bool): Flag indicating whether the editor is in window command mode.
    """

    def __init__(self) -> None:
        """Initialize the Editor with configuration and setup attributes."""
        self.app: Application | None = None
        self.config: "Config" = container["Config"]
        self.bindings: "EditorBindings" = container["EditorBindings"]
        self.wm: "WindowManager" = container["WindowManager"]
        self.style: "EditorStyle" = container["EditorStyle"]

        self._window_command_mode = False

    async def run(self, args: "Namespace") -> None:
        """Run the editor with the provided command-line arguments.

        Args:
            args (Namespace): Command-line arguments used to configure editor behavior.
        """
        self.bindings.init_default_bindings()

        self.app = Application(
            layout=None,
            style=DynamicStyle(self.style.get_style),
            cursor=ModalCursorShapeConfig(),
            clipboard=PyperclipClipboard()
            if self.config.use_system_clipboard
            else InMemoryClipboard(),
            enable_page_navigation_bindings=True,
            key_bindings=self.bindings.kb,
            editing_mode=EditingMode.VI,
            color_depth=lambda: self.config.color_depth,
            mouse_support=True,
            full_screen=True,
        )

        self.app.timeoutlen = 0
        self.app.ttimeoutlen = 0

        await self._init_layout(args)

        await self.app.run_async(pre_run=self._pre_run)

    async def quit(self) -> None:
        """Exit the application."""
        self.app.exit()

    def _pre_run(self) -> None:
        """Set up the application state before entering the main loop."""
        if self.app:
            self.app.vi_state.input_mode = InputMode.NAVIGATION

    async def _init_layout(self, args: "Namespace") -> None:
        """Initialize the layout based on the provided arguments.

        Args:
            args (Namespace): Command-line arguments used to configure layout.
        """
        windows: list["EditorWindow"] = []

        if not args.files:
            first_buffer: "EditorBuffer" = await self.wm.create_buffer("untitled")
            first_window = self.wm.create_window(first_buffer)
            windows.append(first_window)
            self.wm.active_window = first_window
        else:
            first_window = None
            for i, file in enumerate(args.files):
                buffer = await self.wm.create_buffer(file)
                if i == 0:
                    first_window = self.wm.create_window(buffer)
                    windows.append(first_window)
                    self.wm.active_window = first_window
                elif args.open_split or args.open_vsplit:
                    await self.wm.split(
                        self.wm.active_window,
                        is_horizontal=args.open_split,
                        new_buffer=buffer,
                    )
                    windows.append(self.wm.active_window)
                else:
                    first_window.add_buffer(buffer)

        if len(windows) == 1:
            root: "SplitContainer" = container["SplitContainer"](
                [windows[0]], is_horizontal=True
            )
        else:
            root: "SplitContainer" = container["SplitContainer"](
                windows, is_horizontal=not args.open_vsplit
            )

        self.wm.set_layout(root)
        self.app.layout = self.wm.create_layout()
        self.app.layout.focus(self.wm.active_window.active_buffer.buffer)

    @property
    def initialized(self) -> bool:
        """Check if the application has been initialized.

        Returns:
            bool: True if the application is initialized, otherwise False.
        """
        return self.app is not None

    def enter_command_mode(self) -> None:
        """Enter command mode in the editor."""
        if (bar := self.wm.get_bar_by_id("command_bar")) is not None:
            bar.focus()
            self.app.vi_state.input_mode = InputMode.INSERT

    def leave_command_mode(self) -> None:
        """Exit command mode in the editor."""
        if (bar := self.wm.get_bar_by_id("command_bar")) is not None:
            bar.buffer.text = ""
        self.app.layout.focus_last()

    def get_command_mode_input(self) -> str:
        """Retrieve the current input from the command mode.

        Returns:
            str: The command currently entered.
        """
        if (bar := self.wm.get_bar_by_id("command_bar")) is not None:
            return bar.command
        return ""

    def enter_window_command_mode(self) -> None:
        """Enter window command mode."""
        self._window_command_mode = True

    def leave_window_command_mode(self) -> None:
        """Exit window command mode."""
        self._window_command_mode = False

    def is_in_window_command_mode(self) -> bool:
        """Check if the editor is in window command mode.

        Returns:
            bool: True if in window command mode, otherwise False.
        """
        return self._window_command_mode

    def is_in_command_mode(self) -> bool:
        """Check if the editor is currently in command mode.

        Returns:
            bool: True if in command mode, otherwise False.
        """
        if (bar := self.wm.get_bar_by_id("command_bar")) is not None:
            return bar.focused()

    def show_message(self, message: str) -> None:
        """Display a message in the message bar.

        Args:
            message (str): The message to display.
        """
        if (bar := self.wm.get_bar_by_id("message_bar")) is not None:
            bar.message = message

    def has_message(self) -> bool:
        """Check if a message is currently displayed.

        Returns:
            bool: True if a message is displayed, otherwise False.
        """
        if (bar := self.wm.get_bar_by_id("message_bar")) is not None:
            return bool(bar.message)
        return False
