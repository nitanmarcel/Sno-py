from typing import AsyncGenerator, Iterable

from markdown import markdown
from prompt_toolkit import HTML
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from sansio_lsp_client import CompletionItemKind, MarkupContent

from sno_py.fonts_utils import get_icon

completion_symbols_plain = {
    CompletionItemKind.TEXT: "\u005f",
    CompletionItemKind.METHOD: "\u21d2",
    CompletionItemKind.FUNCTION: "\u0192",
    CompletionItemKind.CONSTRUCTOR: "\u22c6",
    CompletionItemKind.FIELD: "\u00b7",
    CompletionItemKind.VARIABLE: "\u0078",
    CompletionItemKind.CLASS: "\u29c9",
    CompletionItemKind.INTERFACE: "\u21d4",
    CompletionItemKind.MODULE: "\u25a9",
    CompletionItemKind.PROPERTY: "\u2318",
    CompletionItemKind.UNIT: "\u03c5",
    CompletionItemKind.VALUE: "\u2208",
    CompletionItemKind.ENUM: "\u2460",
    CompletionItemKind.KEYWORD: "\u27b2",
    CompletionItemKind.SNIPPET: "\u2192",
    CompletionItemKind.COLOR: "\u25a0",
    CompletionItemKind.FILE: "\u25a1",
    CompletionItemKind.REFERENCE: "\u2605",
    CompletionItemKind.FOLDER: "\u25b1",
    CompletionItemKind.ENUMMEMBER: "\u26ac",
    CompletionItemKind.CONSTANT: "\u03c0",
    CompletionItemKind.STRUCT: "\u25a4",
    CompletionItemKind.EVENT: "\u2690",
    CompletionItemKind.OPERATOR: "\u220f",
    CompletionItemKind.TYPEPARAMETER: "\u03b1",
    "signature": "(\u2026)",
}

completion_symbols_nerd = {
    CompletionItemKind.TEXT: "cod-symbol_string",
    CompletionItemKind.METHOD: "cod-symbol_method",
    CompletionItemKind.FUNCTION: "cod-symbol_method",
    CompletionItemKind.CONSTRUCTOR: "cod-symbol_method",
    CompletionItemKind.FIELD: "cod-symbol_field",
    CompletionItemKind.VARIABLE: "cod-symbol_variable",
    CompletionItemKind.CLASS: "cod-symbol_class",
    CompletionItemKind.INTERFACE: "cod-symbol_interface",
    CompletionItemKind.MODULE: "cod-symbol_namespace",
    CompletionItemKind.PROPERTY: "cod-symbol_property",
    CompletionItemKind.UNIT: "cod-symbol_misc",
    CompletionItemKind.VALUE: "cod-symbol_misc",
    CompletionItemKind.ENUM: "cod-symbol_enum",
    CompletionItemKind.KEYWORD: "cod-symbol_keyword",
    CompletionItemKind.SNIPPET: "cod-symbol_snippet",
    CompletionItemKind.COLOR: "cod-symbol_color",
    CompletionItemKind.FILE: "cod-symbol_file",
    CompletionItemKind.REFERENCE: "cod-symbol_misc",
    CompletionItemKind.FOLDER: "cod-symbol_misc",
    CompletionItemKind.ENUMMEMBER: "cod-symbol_enum_member",
    CompletionItemKind.CONSTANT: "cod-symbol_constant",
    CompletionItemKind.STRUCT: "cod-symbol_structure",
    CompletionItemKind.EVENT: "cod-symbol_event",
    CompletionItemKind.OPERATOR: "cod-symbol_operator",
    CompletionItemKind.TYPEPARAMETER: "cod-symbol_misc",
    "signature": "cod-symbol_misc",
}


def get_symbol(kind, use_nerd):
    if use_nerd:
        return get_icon(completion_symbols_nerd[kind])
    return completion_symbols_plain[kind]


class LanguageCompleter(Completer):
    def __init__(self, editor, file_path) -> None:
        self._editor = editor
        self._file_path = file_path
        self._lsp = editor.lsp

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        return super().get_completions(document, complete_event)

    async def get_completions_async(
        self, document: Document, complete_event: CompleteEvent
    ) -> AsyncGenerator[Completion, None]:
        if (client := self._lsp.get_client_if_exists(self._file_path)) is not None:
            signature = (
                await client.request_signature(
                    file_path=self._file_path,
                    line=document.cursor_position_row,
                    character=document.cursor_position_col,
                )
                if document.char_before_cursor in client.signature_triggers
                else None
            )
            if signature:
                yield Completion(
                    text=" ",
                    start_position=0,
                    display=get_symbol("signature", self._editor.use_nerd_fonts)
                    + " "
                    + signature,
                )
            else:
                async for completion in client.request_completion(
                    file_path=self._file_path,
                    line=document.cursor_position_row,
                    character=document.cursor_position_col,
                ):
                    yield Completion(
                        text=completion.insertText or completion.label,
                        start_position=-len(document.get_word_before_cursor()),
                        display=get_symbol(completion.kind, self._editor.use_nerd_fonts)
                        + " "
                        + completion.label,
                        display_meta=(
                            HTML(markdown(completion.documentation.value))
                            if isinstance(completion.documentation, MarkupContent)
                            else completion.documentation
                        ),
                    )
