from typing import AsyncGenerator, Iterable, Union, TYPE_CHECKING

from prompt_toolkit.completion import CompleteEvent, Completer
from prompt_toolkit.completion.base import Completion
from prompt_toolkit.document import Document
from prompt_toolkit.filters import vi_insert_mode
from sansio_lsp_client import CompletionItemKind
from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.config import Config
    from sno_py.window import WindowManager
    from sno_py.buffer import EditorBuffer
    from sno_py.lsp.client import LspClient
    from sansio_lsp_client import SignatureInformation, CompletionItem

completion_symbols_nerd = {
    CompletionItemKind.TEXT: "",
    CompletionItemKind.METHOD: "",
    CompletionItemKind.FUNCTION: "",
    CompletionItemKind.CONSTRUCTOR: "",
    CompletionItemKind.FIELD: "",
    CompletionItemKind.VARIABLE: "",
    CompletionItemKind.CLASS: "",
    CompletionItemKind.INTERFACE: "",
    CompletionItemKind.MODULE: "",
    CompletionItemKind.PROPERTY: "",
    CompletionItemKind.UNIT: "",
    CompletionItemKind.VALUE: "",
    CompletionItemKind.ENUM: "",
    CompletionItemKind.KEYWORD: "",
    CompletionItemKind.SNIPPET: "",
    CompletionItemKind.COLOR: "",
    CompletionItemKind.FILE: "",
    CompletionItemKind.REFERENCE: "",
    CompletionItemKind.FOLDER: "",
    CompletionItemKind.ENUMMEMBER: "",
    CompletionItemKind.CONSTANT: "",
    CompletionItemKind.STRUCT: "",
    CompletionItemKind.EVENT: "",
    CompletionItemKind.OPERATOR: "",
    CompletionItemKind.TYPEPARAMETER: "",
    "signature": "",
}


class LspCompleter(Completer):
    """A completer that integrates with the Language Server Protocol (LSP) to provide suggestions.

    Attributes:
        wm (WindowManager | None): The current window manager instance.
    """

    def __init__(self) -> None:
        """Initialize the LspCompleter."""
        super().__init__()
        self.wm: Union["WindowManager", None] = None

    async def get_completions_async(
        self, document: Document, complete_event: CompleteEvent
    ) -> AsyncGenerator[Completion, None]:
        """Asynchronously yield completions from the LSP server.

        Args:
            document (Document): The current document.
            complete_event (CompleteEvent): The event triggering the completion.

        Yields:
            AsyncGenerator[Completion, None]: Completions provided by LSP.
        """
        if not vi_insert_mode():
            return
        if self.wm is None:
            self.wm = container["WindowManager"]
        buff: Union["EditorBuffer", None] = self.wm.active_window.active_buffer
        if not buff:
            return
        lsp: "LspClient" = buff.lsp
        if not lsp:
            return

        signature: Union["SignatureInformation", None] = (
            await lsp.request_signature(
                file_path=str(buff.location),
                line=buff.buffer.document.cursor_position_row,
                character=buff.buffer.document.cursor_position_col,
            )
            if buff.buffer.document.current_line_before_cursor in lsp.signature_triggers
            else None
        )

        if signature:
            yield Completion(
                text=" ",
                start_position=0,
                display=signature.label,
                display_meta=self._parse_signature_label(signature),
            )
        else:
            completion: "CompletionItem"
            async for completion in lsp.request_completion(
                file_path=buff.location,
                line=buff.buffer.document.cursor_position_row,
                character=buff.buffer.document.cursor_position_col,
            ):
                yield Completion(
                    text=completion.insertText or completion.label,
                    start_position=-len(buff.buffer.document.get_word_before_cursor()),
                    display=self._parse_completion_label(completion),
                )

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Provide completions synchronously.

        Args:
            document (Document): The current document.
            complete_event (CompleteEvent): The event triggering the completion.

        Returns:
            Iterable[Completion]: An iterable of completion suggestions.
        """
        return super().get_completions(document, complete_event)

    @staticmethod
    def _parse_signature_label(signature: "SignatureInformation") -> Union[str, None]:
        """Parse and return the signature label.

        Args:
            signature (SignatureInformation): Signature information from LSP.

        Returns:
            str | None: Parsed signature label if available.
        """
        params = [p.label for p in signature.parameters if isinstance(p.label, str)]
        return params or None

    @staticmethod
    def _parse_completion_label(completion_item: "CompletionItem") -> str:
        """Parse and return an appropriate completion label.

        Args:
            completion_item (CompletionItem): A completion item from LSP.

        Returns:
            str: The label formatted with symbols if configured.
        """
        config: "Config" = container["Config"]
        if config.use_nerd_icons and completion_item.kind:
            return (
                completion_symbols_nerd[completion_item.kind]
                + " "
                + completion_item.label
            )
        return completion_item.label
