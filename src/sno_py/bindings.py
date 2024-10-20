from typing import TYPE_CHECKING
from prompt_toolkit.filters import (
    Condition,
    is_searching,
    vi_insert_mode,
    vi_navigation_mode,
)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPress, KeyPressEvent
from prompt_toolkit.keys import Keys

if TYPE_CHECKING:
    from sno_py.editor import Editor
    from sno_py.buffer import EditorBuffer
    from sno_py.commands.handler import CommandHandler

from sno_py.di import container


class EditorBindings:
    """Defines key bindings and their associated actions for the editor context.

    Attributes:
        kb (KeyBindings): An object to manage and store the key bindings.
        add (Callable): A method that adds key bindings to the KeyBindings object.
    """

    def __init__(self) -> None:
        """Initialize the EditorBindings with the default key bindings."""
        self.kb = KeyBindings()
        self.add = self.kb.add

    def init_default_bindings(self) -> None:
        """Initialize and add default key bindings for the editor."""
        editor: "Editor" = container["Editor"]

        @self.add(Keys.Tab, filter=vi_insert_mode)
        async def _intend(_) -> None:
            active_buffer: "EditorBuffer" = editor.wm.active_window.active_buffer
            if active_buffer:
                if editor.config.expandtabs:
                    active_buffer.buffer.insert_text(" " * editor.config.tabstop)
                else:
                    active_buffer.buffer.insert_text("\t")

        @self.add("g", filter=vi_navigation_mode)
        async def _go_top(_) -> None:
            """Move the cursor to the top of the buffer when 'g' is pressed in navigation mode."""
            editor.wm.active_window.active_buffer.buffer.cursor_position = 0

        @self.add(
            ":",
            filter=Condition(lambda: not editor.is_in_command_mode())
            & ~is_searching
            & ~vi_insert_mode,
        )
        async def _enter_command_mode(_) -> None:
            """Enter command mode when ':' is pressed outside of command mode."""
            editor.enter_command_mode()

        @self.add(Keys.Escape, filter=Condition(lambda: editor.is_in_command_mode()))
        @self.add(
            Keys.Backspace,
            filter=Condition(lambda: editor.is_in_command_mode())
            & Condition(lambda: editor.get_command_mode_input() == ""),
        )
        async def _leave_command_mode(_) -> None:
            """Leave command mode when Escape is pressed or Backspace is pressed on an empty command."""
            editor.leave_command_mode()

        @self.add(Keys.Enter, filter=Condition(lambda: editor.is_in_command_mode()))
        async def _execute_command(_) -> None:
            """Execute the command when Enter is pressed in command mode."""
            cmd = editor.get_command_mode_input()
            if not cmd:
                editor.leave_command_mode()
                return
            handler: "CommandHandler" = container["CommandHandler"]
            editor.leave_command_mode()
            await handler.run(cmd)

        @self.add(Keys.Any, filter=Condition(lambda: editor.has_message()))
        async def _clear_message(e: KeyPressEvent) -> None:
            """Clear any displayed message and process the key press."""
            editor.show_message("")
            key = KeyPress(Keys.Any, e.data)
            e.key_processor.feed(key)
            e.key_processor.process_keys()

        @self.kb.add(
            "c-w",
            filter=~Condition(lambda: editor.is_in_command_mode())
            & ~is_searching
            & ~vi_insert_mode,
        )
        def enter_window_command_mode(_) -> None:
            """Enter window command mode when Ctrl+W is pressed."""
            editor.enter_window_command_mode()

        @self.kb.add("h", filter=Condition(lambda: editor.is_in_window_command_mode()))
        @self.kb.add(
            "left", filter=Condition(lambda: editor.is_in_window_command_mode())
        )
        def focus_previous_window(_) -> None:
            """Focus the previous window when 'h' or left arrow is pressed in window command mode."""
            editor.wm.focus_previous_window()
            editor.leave_window_command_mode()

        @self.kb.add("l", filter=Condition(lambda: editor.is_in_window_command_mode()))
        @self.kb.add(
            "right", filter=Condition(lambda: editor.is_in_window_command_mode())
        )
        def focus_next_window(_) -> None:
            """Focus the next window when 'l' or right arrow is pressed in window command mode."""
            editor.wm.focus_next_window()
            editor.leave_window_command_mode()

        @self.kb.add("j", filter=Condition(lambda: editor.is_in_window_command_mode()))
        @self.kb.add(
            "down", filter=Condition(lambda: editor.is_in_window_command_mode())
        )
        def focus_window_below(_) -> None:
            """Focus the window below when 'j' or down arrow is pressed in window command mode."""
            editor.wm.focus_next_window()
            editor.leave_window_command_mode()

        @self.kb.add("k", filter=Condition(lambda: editor.is_in_window_command_mode()))
        @self.kb.add("up", filter=Condition(lambda: editor.is_in_window_command_mode()))
        def focus_window_above(_) -> None:
            """Focus the window above when 'k' or up arrow is pressed in window command mode."""
            editor.wm.focus_previous_window()
            editor.leave_window_command_mode()

        @self.kb.add(
            Keys.Any, filter=Condition(lambda: editor.is_in_window_command_mode())
        )
        def exit_window_command_mode(e: KeyPressEvent) -> None:
            """Exit window command mode and process the key press for any other key."""
            editor.leave_window_command_mode()
            try:
                key = KeyPress(Keys.Any, e.data)
                e.key_processor.feed(key)
                e.key_processor.process_keys()
            except Exception:
                pass
