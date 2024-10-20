from typing import List
from prompt_toolkit.layout import AnyContainer

from sno_py.di import container


class BarsStorage:
    def __init__(self) -> None:
        self._top_bars: List[AnyContainer] = []
        self._bottom_bars: List[AnyContainer] = []

    def add_top_bar(self, cls: AnyContainer) -> None:
        """Add a bar to the storage. Bars are created when the window has been initialized

        Args:
            cls (AnyContainer): Bar class
        """
        self._top_bars.append(cls)

    def remove_top_bar(self, cls: AnyContainer) -> None:
        """Remove a bar class

        Args:
            cls (AnyContainer): Bar class
        """
        self._top_bars = [b for b in self._top_bars if not cls == b]

    def get_top_bars(self) -> List[AnyContainer]:
        default_bars: List[AnyContainer] = [container["TabBar"]()]
        return default_bars + [b() for b in self._top_bars]

    def add_bottom_bar(self, cls: AnyContainer) -> None:
        """Add a bar to the storage. Bars are created when the window has been initialized

        Args:
            cls (AnyContainer): Bar class
        """
        self._bottom_bars.append(cls)

    def remove_bottom_bar(self, cls: AnyContainer) -> None:
        """Remove a bar class

        Args:
            cls (AnyContainer): Bar class
        """
        self._bottom_bars = [b for b in self._bottom_bars if not cls == b]

    def get_bottom_bars(self) -> List[AnyContainer]:
        default_bars: List[AnyContainer] = [
            container["StatusBar"](),
            container["CommandBar"](),
            container["MessageBar"](),
            container["LspReporterBar"](),
            container["SearchBar"](),
        ]

        return default_bars + [b() for b in self._bottom_bars]
