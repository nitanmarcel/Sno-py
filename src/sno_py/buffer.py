import os
from asyncio import Event
from itertools import count
from typing import TypeVar

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.lexers import SimpleLexer
from sansio_lsp_client import DiagnosticSeverity, PublishDiagnostics

from sno_py.lexer import FileLexer
from sno_py.lsp.completion import LanguageCompleter
from sno_py.lsp.diagnostic import Diagnostic

SnooBuffer = TypeVar("SnooBuffer")


class FileBuffer:
    def __init__(self, editor, path, encoding: str = "UTF-8") -> None:
        self._editor = editor
        self._path = os.path.abspath(path)
        self._name = os.path.basename(path)
        self._encoding = encoding
        self._read_only = False

        self._index = len(self._editor.buffers) - 1 if self._editor.buffers else 0

        self._text = ""

        self._lsp_client = None

        self._version = count()

        self._buffer = Buffer(
            multiline=True,
            document=Document(self._text, 0),
            read_only=self._read_only,
            completer=LanguageCompleter(self._editor, self._path),
            complete_while_typing=True,
            on_text_changed=self._on_text_changed,
        )

        self._lexer = FileLexer(self._editor, self._path)
        self._reports = Diagnostic()
        self._report_task = None
        self._cancelation_token = Event()

    @property
    def buffer(self) -> SnooBuffer:
        return self

    @property
    def _is_new(self) -> bool:
        return not os.path.exists(self._path)

    @property
    def content(self) -> str:
        return self._text

    @property
    def path(self) -> str:
        return self._path

    @property
    def lexer(self) -> str:
        return self._lexer

    @property
    def display_name(self) -> str:
        return self._name

    @property
    def display_name_with_index(self) -> str:
        return f"[{self.index}] {self._name}"

    @display_name.setter
    def display_name(self, name: str) -> str:
        self._name = name
        return self._name

    @property
    def index(self) -> int:
        return self._index

    @property
    def saved(self) -> bool:
        return self._text == self._buffer.text

    @property
    def read_only(self) -> bool:
        return self._read_only

    async def focus(self) -> None:
        if (
            lsp_client := await self._editor.lsp.get_client(self._path, os.getcwd())
        ) is not None and self._lsp_client is None:
            self._lsp_client = lsp_client
            self._lsp_client.open_document(
                self._editor.filetype.guess_filetype(
                    self._path, self._buffer.document.text
                ),
                self._path,
                self._text,
            )
            self._lsp_client.add_notification_handler(
                of_type=PublishDiagnostics, func=self.listen_for_reports
            )

    async def unfocus(self) -> None:
        if self._lsp_client is None:
            self._lsp_client = await self._editor.lsp.get_server()

            self._lsp_client.close_document(self._path)
            self._lsp_client.remove_notification_handler(
                of_type=PublishDiagnostics, func=self.listen_for_reports
            )

    async def save(self) -> bool:
        if self._lsp_client is not None:
            self._lsp_client.save_document(self._path)
        if self._read_only:
            return False
        with open(self._path, "w", encoding=self._encoding) as f:
            self._text = self._buffer.text
            f.write(self._buffer.text)
            return True

    async def load(self) -> None:
        if not self._is_new:
            try:
                with open(self._path, "r+") as f:
                    self._text = f.read()
                    self._buffer.text = self._text
            except PermissionError:
                self._read_only = True
                with open(self._path, "r") as f:
                    self._text = f.read()
                    self._buffer.text = self._text
        if (
            lsp_client := await self._editor.lsp.get_client(self._path, os.getcwd())
        ) is not None:
            self._lsp_client = lsp_client
            self._lsp_client.open_document(
                self._editor.filetype.guess_filetype(
                    self._path, self._buffer.document.text
                ),
                self._path,
                self._text,
            )
            self._lsp_client.add_notification_handler(
                of_type=PublishDiagnostics, func=self.listen_for_reports
            )
            self._lsp_client.remove_notification_handler(
                of_type=PublishDiagnostics, func=self.listen_for_reports
            )

    async def close(self):
        if self._lsp_client is not None:
            self._lsp_client.close_document(self._path)

    def write(self, text: str) -> None:
        pass

    def flush(self) -> None:
        pass

    def clear(self) -> None:
        pass

    async def on_focus() -> None:
        pass

    def reindex(self):
        for i, buffer in enumerate(self._editor.buffers):
            if buffer == self:
                self._index = i

    @property
    def buffer_inst(self) -> Buffer:
        return self._buffer

    def _on_text_changed(self, _):
        if self._lsp_client is not None:
            self._lsp_client.change_document(
                self._path,
                version=next(self._version),
                text=self._buffer.text,
                want_diagnostics=True,
            )

    async def listen_for_reports(self, ev):
        if self._lsp_client is not None:
            with self._reports:
                for diagnostic in ev.diagnostics:
                    if diagnostic.severity == DiagnosticSeverity.ERROR:
                        self._reports.append(diagnostic)

    def reports(self):
        return self._reports.get_diagnostics()


class DebugBuffer(FileBuffer):
    def __init__(self, editor) -> None:
        self._editor = editor
        self._path = "*debug*"
        self._name = "*debug*"
        self._lexer = SimpleLexer()
        self._encoding = "utf-8"
        self._read_only = False

        self._index = -1

        self._text = ""

        self._buffer = Buffer(
            multiline=True,
            document=Document(self._text, 0),
            read_only=False,
            on_text_changed=self._on_text_changed,
        )

    @property
    def _is_new(self) -> bool:
        return True

    async def focus(self) -> None:
        return

    async def unfocus(self) -> None:
        return

    async def save(self) -> bool:
        return

    async def load(self) -> None:
        return

    async def close(self) -> None:
        return

    def write(self, text: str) -> None:
        self._text += text + "\n"
        self._buffer.text = self._text

    def clear(self) -> None:
        self._text = ""
        self._buffer.text = self._text

    def _on_text_changed(self, _):
        if self._buffer.document.text != self._text:
            self._buffer.text = self._text

    def reports(self) -> list:
        return []


class LogBuffer(DebugBuffer):
    def __init__(self, editor) -> None:
        super().__init__(editor)
        self._name = ""

    def focus(self) -> None:
        self._editor.focus_log_buffer()

    def unfocus(self) -> None:
        self._editor.unfocus_log_buffer()
