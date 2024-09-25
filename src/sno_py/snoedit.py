import os

import xonsh.built_ins
import xonsh.execer
import xonsh.imphooks
import xonsh.environ

from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Optional

from appdirs import user_cache_dir, user_config_dir, user_data_dir
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from prompt_toolkit.clipboard.in_memory import InMemoryClipboard
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.filters import has_focus
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from pygments.styles import get_style_by_name
from pygments.token import String

from sno_py.singleton import singleton
from sno_py.bindings import SnoBinds
from sno_py.buffer import DebugBuffer, FileBuffer, LogBuffer, SnooBuffer
from sno_py.layout import SnoLayout
from sno_py.snocommand import SnoCommand
from sno_py.strings import get_string
from sno_py.color_utils import adjust_color_brightness
from sno_py.lsp.manager import LanguageClientManager

from asyncer import asyncify

@singleton
class SnoEdit(object):
    def __init__(self) -> None:
        self.data_dir = user_data_dir("sno.py")
        self.config_dir = user_config_dir("sno.py")
        self.cache_dir = user_cache_dir("snoo.py")
        self.home_dir = Path.home()

        self._create_base_dirs()
        
        self.lsp = LanguageClientManager()
        
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

        self._colorscheme = "monokai"
        self._pygments_class = None 
        self._style: Style = None 

        self._show_line_numbers = True
        self._show_relative_numbers = True
        self._expand_tab = True
        self._tabstop = 4
        self._display_unprintable_characters = True
        self._use_system_clipboard = True
         
        execer = xonsh.execer.Execer()
        xonsh.built_ins.XSH.load(execer=execer, inherit_env=True)
        xonsh.imphooks.install_import_hooks(execer=execer) 
 
        self.app: Application = None
        
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
        
        await self._load_snorc_async()
        
        self.app = Application(layout=self.layout.layout, style=self.style, clipboard=self.clipboard,
                               key_bindings=self.bindings, full_screen=True, editing_mode=EditingMode.VI)
        
        await self.active_buffer.focus() 
        await self.app.run_async(pre_run=pre_run)
    
     
    @property
    def colorscheme(self) -> str:
        return self._colorscheme
    
    @colorscheme.setter
    def colorscheme(self, val) -> None:
        self._colorscheme = val
        self.pygments_class = get_style_by_name(self._colorscheme)
     
    @property
    def pygments_class(self) -> None:
        return self._pygments_class
    
    @pygments_class.setter
    def pygments_class(self, val) -> None:
        self._pygments_class = val
        _style = style_from_pygments_cls(self.pygments_class)
            
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
                _style,
                self._style_extra
            ]
        )
    
    @property
    def style(self) -> Style:
        if not self._style:
            self.colorscheme = self._colorscheme
        return self._style
    
    @style.setter
    def style(self, val) -> None:
        self._style = val
        if self.app:
            self.app.style = self._style
        
    @property
    def show_line_numbers(self):
        return self._show_line_numbers

    @show_line_numbers.setter
    def show_line_numbers(self, value):
        self._show_line_numbers = bool(value)
        self.refresh_layout()

    @property
    def show_relative_numbers(self):
        return self._show_relative_numbers

    @show_relative_numbers.setter
    def show_relative_numbers(self, value):
        self._show_relative_numbers = bool(value)
        self.refresh_layout()

    @property
    def expand_tab(self):
        return self._expand_tab

    @expand_tab.setter
    def expand_tab(self, value):
        self._expand_tab = bool(value)
        self.refresh_layout()

    @property
    def tabstop(self):
        return self._tabstop

    @tabstop.setter
    def tabstop(self, value):
        self._tabstop = value
        self.refresh_layout()

    @property
    def display_unprintable_characters(self):
        return self._display_unprintable_characters

    @display_unprintable_characters.setter
    def display_unprintable_characters(self, value):
        self._display_unprintable_characters = bool(value)
        self.refresh_layout()
        
        
    @property
    def use_system_clipboard(self) -> bool:
        return self._use_system_clipboard
    
    @use_system_clipboard.setter
    def use_system_clipboard(self, value) -> None:
        self._use_system_clipboard = bool(value)
        if self.app:
            self.app.clipboard = self.clipboard
    
    @property
    def clipboard(self):
        return PyperclipClipboard() if self._use_system_clipboard else InMemoryClipboard()
    
    def log(self, text: str) -> None:
        self.log_handler.write(text)
        
    def clear_log(self) -> None:
        self.log_handler.clear()
        
    def focus_log_buffer(self) -> None:
        self.app.layout.focus(self.log_buffer)
        self.app.vi_state.input_mode = InputMode.NAVIGATION

    def unfocus_log_buffer(self) -> None:
        self.app.layout.focus_last()
        self.app.vi_state.input_mode = InputMode.INSERT
    
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

    async def create_file_buffer(self, path: str, encoding: str = "utf-8") -> None:
        if not path:
            return
        buffer = FileBuffer(
            self,
            path,
            encoding
        )
        await buffer.load()
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

    async def save_current_buffer(self) -> None:
        if not await self.active_buffer.save():
            self.log(get_string("read_only"))
            return False
        return True

    async def save_all_buffers(self) -> None:
        for b in reversed(self.buffers):
            if not await b.save():
                break

    async def close_current_buffer(self, buffer=None, forced: bool=False) -> bool:
        if not buffer:
            buffer = self.active_buffer
        if buffer.saved or forced:
            if len(self.buffers) == 1:
                await self.buffers[0].close()
                get_app().exit()
                return True
            else:
                index = self.get_buffer_index(path=buffer.path)
                buffer = self.buffers.pop(index)
                await buffer.close()
                self.active_buffer = self.buffers[index-1]
                self.refresh_layout()
                return True
        else:
            if len(self.buffers) > 1:
                await self.select_buffer(path=buffer.path)
            self.log(get_string("not_saved"))
            return False

    async def close_all_buffers(self, forced: bool=False) -> bool:
        for b in reversed(self.buffers):
            if not await self.close_current_buffer(buffer=b, forced=forced):
                break

    def refresh_layout(self) -> None:
        if self.app:
            self.app.layout = self.layout.layout

    def _load_snorc(self) -> None:
        if os.path.isfile(self.home_dir / ".snorc"):
            with open(self.home_dir / ".snorc") as rc:
                with redirect_stdout(self.debug_buffer):
                    with redirect_stderr(self.debug_buffer):
                        xonsh.built_ins.XSH.builtins.execx(rc.read(), glbs={"editor": self})
    
    async def _load_snorc_async(self) -> None:
        await asyncify(self._load_snorc)()
    
    def execx(self, code) -> None:
        xonsh.built_ins.XSH.builtins.execx(code, glbs={"editor": self})
    
    async def aexecx(self, code) -> None:
        await asyncify(self.execx)(code)