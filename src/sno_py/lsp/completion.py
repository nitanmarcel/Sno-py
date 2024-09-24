import asyncio

from typing import AsyncGenerator, Iterable

from prompt_toolkit.completion import Completer, CompleteEvent, Completion
from prompt_toolkit.completion.word_completer import WordCompleter
from prompt_toolkit.document import Document
import sansio_lsp_client as lsp

class LanguageCompleter(Completer):
    def __init__(self, editor, file_path) -> None:
        self._editor = editor
        self._file_path = file_path
        self._lsp = editor.lsp
        
    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        return super().get_completions(document, complete_event) 
     
    async def get_completions_async(self, document: Document, complete_event: CompleteEvent) -> AsyncGenerator[Completion, None]:
        if (client := self._lsp.get_client_if_exists(self._file_path)) is not None:
            async for completion in client.request_completion(file_path=self._file_path, line=document.cursor_position_row, character=document.cursor_position_col):
                yield Completion(
                    text=completion.insertText,
                    start_position=-len(document.get_word_before_cursor()),
                    display=completion.label,
                    display_meta=completion.documentation
                )
 