import os
import stat
from typing import TypeVar

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory

SnooBuffer = TypeVar("SnooBuffer")


class FileBuffer:
    def __init__(self, editor, path, encoding: str="UTF-8") -> None:
        self._editor = editor
        self._path = os.path.abspath(path)
        self._name = os.path.basename(path)
        self._encoding = encoding
        self._read_only = False

        self._text = self.load() if not self._is_new else ""

        self._buffer = Buffer(
            multiline=True,
            document=Document(self._text, 0),
            read_only=self._read_only,
            completer=self._editor.buffer_completer,
            complete_while_typing=bool(self._editor.buffer_completer)
        )

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
    def display_name(self) -> str:
        return self._name

    @display_name.setter
    def display_name(self, name: str) -> str:
        self._name = name
        return self._name

    @property
    def saved(self) -> bool:
        return self._text == self._buffer.text

    @property
    def read_only(self) -> bool:
        return self._read_only

    def save(self) -> bool:
        if self._read_only:
            return False
        with open(self._path, "w", encoding=self._encoding) as f:
            self._text = self._buffer.text
            f.write(self._buffer.text)
            return True

    def load(self) -> None:
        try:
            with open(self._path, "r+") as f:
                return f.read()
        except PermissionError:
            self._read_only = True
            with open(self._path, "r") as f:
                return f.read()

    def write(self, text: str) -> None:
        self._buffer.text = text

    def flush(self) -> None:
        pass

    def clear(self) -> None:
        self._text = ""
        self._buffer.reset()

    @property
    def buffer_inst(self) -> Buffer:
        return self._buffer


class DebugBuffer:
    def __init__(self, editor, encoding: str = "utf-8") -> None:
        self._editor = editor
        self._name = "*debug*"
        self._encoding = encoding

        self._text = ""

        self._buffer = Buffer(
            multiline=True,
            document=Document(self._text, 0),
            on_text_changed=self.text_changed
        )

    @property
    def buffer(self) -> SnooBuffer:
        return self

    @property
    def _is_new(self) -> bool:
        return True

    @property
    def content(self) -> str:
        return self._text

    @property
    def display_name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return "/dev/null"

    @property
    def saved(self) -> bool:
        return False

    def save(self) -> None:
        return False

    def load(self) -> None:
        pass

    def write(self, text: str) -> None:
        self._text += "\n" + \
            text.decode(self._encoding) if isinstance(text, bytes) else text
        self._buffer.text = self._text

    def flush(self) -> None:
        pass

    def clear(self) -> None:
        self._text = ""
        self._buffer.reset()

    @property
    def buffer_inst(self) -> Buffer:
        return self._buffer

    def text_changed(self, _) -> None:
        if self._buffer.text != self._text:
            self._buffer.text = self._text


class LogBuffer(DebugBuffer):
    def __init__(self, editor, encoding: str="utf-8") -> None:
        super().__init__(editor, encoding)
        self._name = ""
