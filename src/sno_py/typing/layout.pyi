from prompt_toolkit.layout.layout import Layout
from sno_py.snoedit import SnoEdit


def _try_char(character: str, backup: str, encoding: str = ...) -> str: ...


class CommandToolBar:
    def __init__(self, editor: SnoEdit) -> None: ...


class LogToolBar:
    def __init__(self, editor: SnoEdit) -> None: ...


class SnoLayout:
    def __init__(self, editor: SnoEdit) -> None: ...
    @property
    def layout(self) -> Layout: ...
