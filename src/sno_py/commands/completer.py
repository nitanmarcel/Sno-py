from typing import TYPE_CHECKING, Callable, Sequence

from prompt_toolkit.completion import Completer, FuzzyWordCompleter, PathCompleter
from prompt_toolkit.contrib.completers import SystemCompleter
from prompt_toolkit.contrib.regular_languages.compiler import compile
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter

from sno_py.di import container
from attrs import fields

if TYPE_CHECKING:
    from sno_py.config import Config


class _FuzyCompletter(FuzzyWordCompleter):
    def __init__(
        self, words: Sequence[str] | Callable[[], Sequence[str]] | None = None
    ) -> None:
        super(_FuzyCompletter, self).__init__(
            words=words or (lambda: container["CommandHandler"].get_command_list())
        )


class _ConfigCompletter(FuzzyWordCompleter):
    def __init__(self) -> None:
        config: "Config" = container["Config"]
        super(_ConfigCompletter, self).__init__(
            words=[f.name for f in fields(config.__class__) if f.name != "colorscheme"]
        )


class _PathCompleter(GrammarCompleter):
    def __init__(self) -> None:
        super(_PathCompleter, self).__init__(
            compiled_grammar=compile("(\S+\s+)?(?P<path>\S*)"),
            completers={"path": PathCompleter(expanduser=True)},
        )


class _SystemCompleter(GrammarCompleter):
    def __init__(self) -> None:
        super(_SystemCompleter, self).__init__(
            compiled_grammar=compile("(\S+\s+)?(?P<system>\S*)"),
            completers={"system": SystemCompleter()},
        )


class CompleteHandler:
    def __init__(self) -> None:
        self.cmd: Completer = _FuzyCompletter()
        self.path: Completer = _PathCompleter()
        self.words: Completer = _FuzyCompletter
        self.config: Completer = _ConfigCompletter()
        self.system: Completer = _SystemCompleter()

    def get_completer(self, name) -> Completer | None:
        if name == "command":
            return self.cmd
        if name in ["path", "file"]:
            return self.path
        if name == "config":
            return self.config
        if name == "system":
            return self.system
