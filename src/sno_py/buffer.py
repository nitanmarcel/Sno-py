from typing import TYPE_CHECKING, Any, Union
from itertools import count
from prompt_toolkit.buffer import Buffer, Document
from prompt_toolkit.application import get_app
from sansio_lsp_client import PublishDiagnostics, DiagnosticSeverity
from anyio import Path

from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.editor import Editor
    from sno_py.filetypes.filetypes import FileType
    from sno_py.lsp.client import LspClient
    from sno_py.lsp.manager import LanguageClientManager
    from sansio_lsp_client import Diagnostic
    from sno_py.lexer import TreeSitterLexer
    from prompt_toolkit.lexers import Lexer


class EditorBuffer:
    """Represents a text buffer in the editor, managing text content, LSP support, and file operations.

    Attributes:
        editor (Editor): Reference to the editor instance.
        location (Path): The file location associated with the buffer.
        text (str): The current text content of the buffer.
        version (count[int]): A version counter for document changes.
        is_new (bool): Flag indicating if the buffer is new (unsaved).
        lexer (Lexer): Lexer for syntax highlighting.
        lsp (LspClient | None): Language Server Protocol client associated with the buffer.
        lsp_reports (list[dict[str, Any]]): List of LSP reports containing diagnostic information.
        buffer (Buffer): The prompt_toolkit buffer managing text input and editing.
    """

    def __init__(self, location: str, text: str) -> None:
        """Initialize the EditorBuffer with a location and initial text.

        Args:
            location (str): The file location path.
            text (str): Initial text content for the buffer.
        """
        self.editor: "Editor" = container["Editor"]
        self.location: Path = Path(location)
        self.abs_location: Union[Path, None] = None
        self.text: str = text
        self.version: count[int] = count()
        self.is_new: bool = True
        lexer_cls: "TreeSitterLexer" = container["TreeSitterLexer"]
        self.lexer: Lexer = lexer_cls.from_file(str(self.location), self.text)
        self.lsp: Union["LspClient", None] = None
        self.lsp_reports: list[dict[str, Any]] = []

        self.buffer: Buffer = Buffer(
            multiline=True,
            document=Document(text, 0),
            complete_while_typing=True,
            completer=container["LspCompleter"],
            on_text_changed=self._notify_lsp_document_change,
        )

    async def read(self) -> None:
        """Read text from the specified file location into the buffer."""
        try:
            try:
                self.text = await self.location.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                self.text = await self.location.read_text(encoding="latin-1")
            self.buffer.set_document(Document(self.text, 0))
            self.is_new = False
            self.reload_document()
            self.abs_location = await self.get_absolute_location()
        except FileNotFoundError:
            self.text = ""
            self.buffer.set_document(Document(self.text, 0))
            self.is_new = True
            self.abs_location = await self.get_absolute_location()
            self.reload_document()
        except IOError as e:
            raise ValueError(f"Error reading file: {e}")

        get_app().create_background_task(self._init_lsp_task())

    async def write(self) -> None:
        """Write text from the buffer to the specified file location."""
        try:
            await self.location.write_text(self.buffer.text)
            self.is_new = False
            self.reload_document()
            if self.lsp is not None:
                self.lsp.save_document(document_path=str(self.abs_location))
        except IOError as e:
            raise ValueError(f"Error writing file: {e}")

    async def _init_lsp_task(self) -> None:
        """Initialize the Language Server Protocol (LSP) client for the buffer."""
        if self.lsp is None:
            manager: "LanguageClientManager" = container["LanguageClientManager"]
            workdir: Path = await Path.cwd()
            self.lsp = await manager.get_client(str(self.location), str(workdir))
            if self.lsp is not None:
                ft: "FileType" = container["FileType"]
                self.lsp.open_document(
                    ft.guess_filetype(self.abs_location, self.buffer.text),
                    str(self.abs_location),
                    self.buffer.text,
                )

                self.lsp.add_notification_handler(
                    PublishDiagnostics, self._lsp_reports_handler
                )

    async def _lsp_reports_handler(self, ev: "PublishDiagnostics") -> None:
        """Handle incoming LSP diagnostic reports for the buffer."""
        reports: list[dict[str, Any]] = []
        diagnostic: "Diagnostic"
        for diagnostic in ev.diagnostics:
            report = {"message": diagnostic.message, "range": diagnostic.range}
            if diagnostic.severity == DiagnosticSeverity.ERROR:
                report["is_error"] = True
                reports.append(report)
            elif diagnostic.severity == DiagnosticSeverity.WARNING:
                report["is_error"] = False
                reports.append(report)
            self.lsp_reports = reports

    def _notify_lsp_document_change(self, _) -> None:
        """Notify the LSP server about changes in the document."""
        if self.lsp is not None:
            self.lsp.change_document(
                file_path=str(self.abs_location),
                version=next(self.version),
                text=self.buffer.text,
                want_diagnostics=True,
            )

    def notify_lsp_document_close(self) -> None:
        """Notify the LSP server that the current document has been closed."""
        if self.lsp is not None:
            self.lsp.close_document(file_path=str(self.abs_location))

    def get_display_name(self, short=True) -> str:
        """Get the display name for the buffer.

        Args:
            short (bool): Whether to return a short name.

        Returns:
            str: The display name of the buffer.
        """
        if short:
            return self.location.name
        return str(self.location)

    async def get_absolute_location(self) -> Path:
        """Get absolute location path in an async"""
        if self.abs_location is None:
            self.abs_location = (
                await self.location.absolute()
                if not (self.location.is_absolute())
                else self.location
            )
        return self.abs_location

    def reload_document(self) -> None:
        """Reload the buffer text from the current buffer content."""
        self.text = self.buffer.text

    @property
    def changed(self) -> bool:
        """Check if the buffer content has changed from the original text.

        Returns:
            bool: True if the buffer has unsaved changes, otherwise False.
        """
        return self.buffer.text != self.text
