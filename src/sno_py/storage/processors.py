import sys
from typing import List, TYPE_CHECKING
from prompt_toolkit.application import get_app
from prompt_toolkit.layout.processors import (
    HighlightSearchProcessor,
    HighlightIncrementalSearchProcessor,
    HighlightSelectionProcessor,
    Processor,
    ShowTrailingWhiteSpaceProcessor,
    DisplayMultipleCursors,
    HighlightMatchingBracketProcessor,
    TabsProcessor,
)

from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.config import Config


class ProcessorsStorage:
    def __init__(self) -> None:
        self._processor_instances: List[Processor] = []

    def add_processors(self, cls: Processor) -> None:
        """Add a processor to the storage. Processors are created when the window has been initialized

        Args:
            cls (Processor): Processor class
        """
        self._processor_instances.append(cls)

    def remove_processor(self, cls: Processor) -> None:
        """Remove a processor class

        Args:
            cls (Processor): Processor class
        """
        self._processor_instances = [
            p for p in self._processor_instances if not cls == p
        ]

    def get_processors(self) -> List[Processor]:
        config: "Config" = container["Config"]
        default_processors = [
            container["LspReportsProcessor"](),
            ShowTrailingWhiteSpaceProcessor(),
            HighlightSelectionProcessor(),
            HighlightSearchProcessor(),
            HighlightIncrementalSearchProcessor(),
            HighlightMatchingBracketProcessor(),
            DisplayMultipleCursors(),
            TabsProcessor(
                tabstop=config.tabstop,
                char1=lambda: "|" if config.show_unprintable_characters else " ",
                char2=lambda: self._try_char("\u2508", ".", get_app().output.encoding())
                if config.show_unprintable_characters
                else " ",
            ),
        ]

        return [p() for p in self._processor_instances] + default_processors

    @staticmethod
    def _try_char(character: str, backup, encoding=sys.stdout.encoding):
        """
        Return `character` if it can be encoded using sys.stdout, else return the
        backup character.
        """
        if character.encode(encoding, "replace") == b"?":
            return backup
        else:
            return character
