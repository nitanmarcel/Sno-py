from functools import cached_property
from typing import TYPE_CHECKING, Union

from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Always, has_focus, is_searching
from prompt_toolkit.layout import ConditionalContainer, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.processors import BeforeInput

from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.commands.handler import CommandHandler


class _CommandBar(ConditionalContainer):
    """A command bar component for the editor that listens for command input.

    Attributes:
        id (str): The unique identifier for the command bar.
        buffer (Buffer): The text buffer backing the command input field.
        command_handler (CommandHandler | None): Handler for command processing.
    """

    def __init__(self, buffer: Buffer) -> None:
        """Initialize the command bar with a given buffer.

        Args:
            buffer (Buffer): The buffer associated with this command bar.
        """
        self.id = "command_bar"
        self.buffer = buffer
        self.buffer.on_text_changed.add_handler(self.cmd_changed)
        self.command_handler: Union["CommandHandler", None] = None

        super(_CommandBar, self).__init__(
            Window(
                BufferControl(
                    buffer=buffer,
                    input_processors=[BeforeInput(":")],
                ),
                height=1,
                style="class:background",
            ),
            filter=has_focus(buffer) & ~is_searching,
        )

    def focus(self) -> None:
        """Focus the command bar."""
        get_app().layout.focus(self.buffer)

    @property
    def focused(self) -> bool:
        """Check if the command bar is focused.

        Returns:
            bool: True if the command bar is focused, otherwise False.
        """
        return has_focus(self.buffer)

    @property
    def command(self) -> str:
        """Get the current command text from the buffer.

        Returns:
            str: The text of the current command in the buffer.
        """
        return self.buffer.text

    def cmd_changed(self, *args, **kwargs) -> None:
        """Handler triggered when the command text changes."""
        text = self.buffer.text
        if cmd_parts := text.split(None, 1):
            cmd_name = cmd_parts[0]
            if self.command_handler is None:
                self.command_handler = container["CommandHandler"]
            self.buffer.completer = self.command_handler.get_completer(cmd_name)
            self.buffer.complete_while_typing = Always()


class CommandBar:
    """Command bar interface for the editor."""

    def __init__(self) -> None:
        """Initialize the CommandBar with a buffer."""
        self.buffer = Buffer(multiline=False)

    @cached_property
    def container(self) -> ConditionalContainer:
        """Retrieve the conditional container backing the CommandBar.

        Returns:
            ConditionalContainer: The container for the command bar UI component.
        """
        return _CommandBar(self.buffer)
