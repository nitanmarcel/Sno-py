import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Optional

from appdirs import user_cache_dir, user_config_dir, user_data_dir
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.filters import has_focus
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from pygments.styles import get_style_by_name
from pygments.token import String
from xonsh.built_ins import get_default_builtins
from xonsh.execer import Execer

from sno_py.bindings import SnoBinds
from sno_py.buffer import DebugBuffer, FileBuffer, LogBuffer, SnooBuffer
from sno_py.layout import SnoLayout
from sno_py.snocommand import SnoCommand
from sno_py.strings import get_string
from sno_py.color_utils import adjust_color_brightness


class SnoEdit(object):
    def __init__(self) -> None:
        self.data_dir = user_data_dir("sno.py")
        self.config_dir = user_config_dir("sno.py")
        self.cache_dir = user_cache_dir("snoo.py")
        self.home_dir = Path.home()

        self._create_base_dirs()

        self.command_runner = SnoCommand(self)
        self.command_buffer = Buffer(multiline=False, completer=self.command_runner.default_completer,
                                     complete_while_typing=True, on_text_changed=self.command_runner.process_command_completion)

        self.search_buffer = Buffer(multiline=False)

        self.debug_buffer = DebugBuffer(self)

        self.log_handler = LogBuffer(self)
        self.log_buffer = self.log_handler.buffer_inst

        self.buffer_completer: Completer = None

        self.buffers = []
        self.active_buffer = self.debug_buffer

        self.bindings = SnoBinds(self)
        self.layout = SnoLayout(self)

        self.colorscheme = "monokai"
        self.pygments_class = get_style_by_name(self.colorscheme)
        self.style: Style = style_from_pygments_cls(self.pygments_class)

        self.show_line_numbers = True
        self.show_relative_numbers = True
        self.expand_tab = True
        self.tabstop = 4
        self.display_unprintable_characters = True

        self.builtinsx = get_default_builtins(Execer())
        self._load_snorc()

        self._style_extra = Style.from_dict(
            {
                "background": f"bg:{self.pygments_class.background_color}",
                "container": f"bg:{adjust_color_brightness(self.pygments_class.background_color, 1.2)}",
                "completion-menu": f"bg:{adjust_color_brightness(self.pygments_class.background_color, 1.2)} {self.pygments_class.styles[String]}",
                "search": f"bg:{self.pygments_class.styles[String]} {self.pygments_class.highlight_color}",
                "selected": f"bg:{self.pygments_class.styles[String]} {self.pygments_class.highlight_color}",
                "completion-menu.completion.current": f"{self.pygments_class.highlight_color}",
            }
        )

        self.style = merge_styles(
            [
                self.style,
                self._style_extra
            ]
        )

        self.app = Application(layout=self.layout.layout, style=self.style,
                               key_bindings=self.bindings, full_screen=True, editing_mode=EditingMode.VI)

    async def enter_command_mode(self) -> None:
        self.app.layout.focus(self.command_buffer)
        self.app.vi_state.input_mode = InputMode.INSERT

    def leave_command_mode(self) -> None:
        self.app.layout.focus_last()
        self.app.vi_state.input_mode = InputMode.NAVIGATION
        self.command_buffer.reset()

    async def process_command(self) -> None:
        command = self.command_buffer.text
        self.leave_command_mode()
        await self.command_runner.run(command)

    def _create_base_dirs(self) -> None:
        for di in [self.data_dir, self.cache_dir, self.config_dir]:
            if not os.path.exists(di):
                os.makedirs(di)

    async def run(self) -> None:
        def pre_run() -> None:
            self.app.vi_state.input_mode = InputMode.NAVIGATION
        await self.app.run_async(pre_run=pre_run)

    def log(self, text: str) -> None:
        self.log_handler.write(text)
        self.app.layout.focus(self.log_buffer)
        self.app.vi_state.input_mode = InputMode.NAVIGATION

    def clear_log(self) -> None:
        self.app.layout.focus_last()
        self.app.vi_state.input_mode = InputMode.INSERT
        self.log_handler.clear()

    def reset_buffers(self) -> None:
        if has_focus(self.command_buffer):
            self.leave_command_mode()
        if has_focus(self.log_buffer):
            self.clear_log()

    def add_buffer(self, buffer: SnooBuffer) -> None:
        if buffer.display_name in [b for b in self.buffers]:
            i = 1
            for b in self.buffers:
                if b.display_name == buffer.display_name:
                    buffer.display_name += f" ({i}) "
                    i += 1
        if len(self.buffers) == 0:
            self.buffers.append(buffer)
        else:
            index = self.get_buffer_index(path=self.active_buffer.path)
            self.buffers.insert(index, buffer)
        self.active_buffer = buffer
        self.refresh_layout()
        if buffer.read_only:
            self.log(get_string("read_only"))

    def create_file_buffer(self, path: str, encoding: str = "utf-8") -> None:
        if not path:
            return
        buffer = FileBuffer(
            self,
            path,
            encoding
        )
        self.add_buffer(buffer)

    def select_buffer(self, path=None, display_name: Optional[str]=None) -> None:
        index = self.get_buffer_index(path=path, display_name=display_name)
        self.active_buffer = self.buffers[index]
        self.refresh_layout()

    def get_buffer_index(self, path=None, display_name: Optional[str]=None) -> Optional[int]:
        for i, buff in enumerate(self.buffers):
            if path and buff.path == path:
                return i
            if display_name and buff.display_name == display_name:
                return i
        return None

    def save_current_buffer(self) -> None:
        if not self.active_buffer.save():
            self.log(get_string("read_only"))
            return False
        return True

    def save_all_buffers(self) -> None:
        for b in reversed(self.buffers):
            if not b.save():
                break

    def close_current_buffer(self, buffer=None, forced: bool=False) -> bool:
        if not buffer:
            buffer = self.active_buffer
        if buffer.saved or forced:
            if len(self.buffers) == 1:
                get_app().exit()
                return True
            else:
                index = self.get_buffer_index(path=buffer.path)
                self.buffers.pop(index)
                self.active_buffer = self.buffers[index-1]
                self.refresh_layout()
                return True
        else:
            if len(self.buffers) > 1:
                self.select_buffer(path=buffer.path)
            self.log(get_string("not_saved"))
            return False

    def close_all_buffers(self, forced: bool=False) -> bool:
        for b in reversed(self.buffers):
            if not self.close_current_buffer(buffer=b, forced=forced):
                break

    def refresh_layout(self) -> None:
        self.app.layout = self.layout.layout

    def _load_snorc(self) -> None:
        if os.path.isfile(self.home_dir / ".snorc"):
            with open(self.home_dir / ".snorc") as rc:
                with redirect_stdout(self.debug_buffer):
                    with redirect_stderr(self.debug_buffer):
                        self.builtinsx.execx(rc.read(), glbs={"snoedit": self})
