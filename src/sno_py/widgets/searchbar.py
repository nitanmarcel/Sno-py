from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Container
from prompt_toolkit.widgets.toolbars import SearchToolbar


class _SearchBar(SearchToolbar):
    """A search bar component providing search functionality with customizable behavior.

    Attributes:
        id (str): The unique identifier for the search bar.
    """

    def __init__(self, buffer: Buffer) -> None:
        """Initialize the search bar with a given buffer in vi mode.

        Args:
            buffer (Buffer): The buffer associated with this search bar.
        """
        self.id = "search_bar"
        super(_SearchBar, self).__init__(search_buffer=buffer, vi_mode=True)

    @property
    def search_control(self):
        """Access the control of the search toolbar.

        Returns:
            The control used by the search toolbar.
        """
        return self.control


class SearchBar:
    """A wrapper for creating search bars with buffers."""

    def __init__(self) -> None:
        """Initialize the SearchBar with a single-line buffer."""
        self.buffer = Buffer(multiline=False)

    @property
    def container(self) -> Container:
        """Retrieve the container backing the SearchBar.

        Returns:
            Container: The container representing the search bar UI component.
        """
        return _SearchBar(self.buffer)
