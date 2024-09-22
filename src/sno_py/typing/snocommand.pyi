from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion.word_completer import WordCompleter
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter
from sno_py.snoedit import SnoEdit
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)


def o(editor: SnoEdit, *args, **kwargs) -> None: ...


def o_completion_handler(
    editor: SnoEdit,
    args: list
) -> GrammarCompleter: ...


def qa(editor: SnoEdit, *args, **kwargs) -> None: ...


def wa(editor: SnoEdit, *args, **kwargs) -> None: ...


class SnoCommand:
    def __init__(self, editor: SnoEdit) -> None: ...
    def _create_defaults(self) -> None: ...
    def _parse_args_kwargs(self, input_str: str) -> Tuple[List[str], Dict[Any, Any]]: ...
    def _parse_command(self, command_input: str) -> List[str]: ...
    def add_command_handler(
        self,
        func: Union[List[Callable], Callable],
        name: str,
        completion_handler: Optional[Callable] = ...,
    ) -> None: ...
    @property
    def default_completer(self) -> WordCompleter: ...
    def get_completion_handler(self, name: str) -> Callable: ...
    def process_command_completion(self, buffer: Buffer) -> None: ...
    async def run(self, command_input: str) -> str: ...
