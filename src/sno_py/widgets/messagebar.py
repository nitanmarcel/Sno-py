from functools import cached_property

from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition, has_focus
from prompt_toolkit.layout import ConditionalContainer, Window
from prompt_toolkit.layout.controls import BufferControl


class _MessageBar(ConditionalContainer):
    """A message bar component for displaying messages that changes visibility based on whether a message is present.

    Attributes:
        id (str): The unique identifier for the message bar.
        buffer (Buffer): The text buffer associated with this message bar.
    """

    def __init__(self, buffer: Buffer) -> None:
        """Initialize the message bar with a given buffer.

        Args:
            buffer (Buffer): The buffer associated with this message bar.
        """
        self.id = "message_bar"
        self.buffer = buffer

        super(_MessageBar, self).__init__(
            Window(
                BufferControl(
                    buffer=buffer,
                ),
                height=1,
                style="class:background",
            ),
            filter=Condition(lambda: bool(self.message)),
        )

    def focus(self) -> None:
        """Focus the message bar."""
        get_app().layout.focus(self.buffer)

    @property
    def focused(self) -> bool:
        """Check if the message bar is focused.

        Returns:
            bool: True if the message bar is focused, otherwise False.
        """
        return has_focus(self.buffer)

    @property
    def message(self) -> str:
        """Get the current message text from the buffer.

        Returns:
            str: The text of the current message.
        """
        return self.buffer.text

    @message.setter
    def message(self, value: str) -> None:
        """Set the message text in the buffer.

        Args:
            value (str): The message to be set.
        """
        self.buffer.text = value


class MessageBar:
    """A wrapper for creating message bars with buffers."""

    def __init__(self) -> None:
        """Initialize the MessageBar with a single-line buffer."""
        self.buffer = Buffer(multiline=False)

    @cached_property
    def container(self) -> ConditionalContainer:
        """Retrieve the conditional container backing the MessageBar.

        Returns:
            ConditionalContainer: The container for the message bar UI component.
        """
        return _MessageBar(self.buffer)
