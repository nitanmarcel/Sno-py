import asyncio

from typing import AsyncGenerator, Iterable

from prompt_toolkit.completion import Completer, CompleteEvent, Completion
from prompt_toolkit.completion.word_completer import WordCompleter
from prompt_toolkit.document import Document
from sansio_lsp_client import CompletionItemKind

completion_symbols_plain = {
    CompletionItemKind.TEXT: "\u005F",
    CompletionItemKind.METHOD: "\u21D2",
    CompletionItemKind.FUNCTION: "\u0192",
    CompletionItemKind.CONSTRUCTOR: "\u22C6",
    CompletionItemKind.FIELD: "\u00B7",
    CompletionItemKind.VARIABLE: "\u0078",
    CompletionItemKind.CLASS: "\u29C9",
    CompletionItemKind.INTERFACE: "\u21D4",
    CompletionItemKind.MODULE: "\u25A9",
    CompletionItemKind.PROPERTY: "\u2318",
    CompletionItemKind.UNIT: "\u03C5",
    CompletionItemKind.VALUE: "\u2208",
    CompletionItemKind.ENUM: "\u2460",
    CompletionItemKind.KEYWORD: "\u27B2",
    CompletionItemKind.SNIPPET: "\u2192",
    CompletionItemKind.COLOR: "\u25A0",
    CompletionItemKind.FILE: "\u25A1",
    CompletionItemKind.REFERENCE: "\u2605",
    CompletionItemKind.FOLDER: "\u25B1",
    CompletionItemKind.ENUMMEMBER: "\u26AC",
    CompletionItemKind.CONSTANT: "\u03C0",
    CompletionItemKind.STRUCT: "\u25A4",
    CompletionItemKind.EVENT: "\u2690",
    CompletionItemKind.OPERATOR: "\u220F",
    CompletionItemKind.TYPEPARAMETER: "\u03B1",
    
    "signature": "(\u2026)"
}

class LanguageCompleter(Completer):
    def __init__(self, editor, file_path) -> None:
        self._editor = editor
        self._file_path = file_path
        self._lsp = editor.lsp
        
    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        return super().get_completions(document, complete_event) 
     
    async def get_completions_async(self, document: Document, complete_event: CompleteEvent) -> AsyncGenerator[Completion, None]:
        if (client := self._lsp.get_client_if_exists(self._file_path)) is not None:
            signature = await client.request_signature(file_path=self._file_path, line=document.cursor_position_row, character=document.cursor_position_col) if document.char_before_cursor in client.signature_triggers else None
            if signature:
                yield Completion(
                    text=" ",
                    start_position=0,
                    display=completion_symbols_plain["signature"] + " " + signature
                )
            else:
                async for completion in client.request_completion(file_path=self._file_path, line=document.cursor_position_row, character=document.cursor_position_col):
                    yield Completion(
                        text=completion.insertText,
                        start_position=-len(document.get_word_before_cursor()),
                        display=completion_symbols_plain[completion.kind] + " " + completion.label,
                        display_meta=completion.documentation
                    )
 