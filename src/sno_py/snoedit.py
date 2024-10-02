import os
import re
import shlex
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import xonsh.built_ins
import xonsh.execer
import xonsh.imphooks
from appdirs import user_cache_dir, user_config_dir, user_data_dir
from prompt_toolkit.eventloop import run_in_executor_with_context
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.clipboard.in_memory import InMemoryClipboard
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from prompt_toolkit.completion import Completer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.filters import has_focus
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from pygments.styles import get_style_by_name
from pygments.token import Error, String

from sno_py.bindings import SnoBinds
from sno_py.buffer import DebugBuffer, FileBuffer, LogBuffer, SnooBuffer
from sno_py.color_utils import adjust_color_brightness
from sno_py.filetypes import FileType
from sno_py.filters import Filters
from sno_py.layout import SnoLayout
from sno_py.lsp.manager import LanguageClientManager
from sno_py.singleton import singleton
from sno_py.snocommand import SnoCommand
from sno_py.strings import get_string

from ptterm.utils import get_default_shell
from prompt_toolkit.output.color_depth import ColorDepth


@singleton
class SnoEdit(object):
    def __init__(self) -> None:
        self.data_dir = user_data_dir("sno.py")
        self.config_dir = user_config_dir("sno.py")
        self.cache_dir = user_cache_dir("snoo.py")
        self.home_dir = Path.home()

        self._create_base_dirs()

        self.filetype = FileType()
        self.filters = Filters(self)
        self.lsp = LanguageClientManager(self)

        self.command_runner = SnoCommand(self)
        self.command_buffer = Buffer(
            multiline=False,
            completer=self.command_runner.default_completer,
            complete_while_typing=True,
            on_text_changed=self.command_runner.process_command_completion,
        )

        self.search_buffer = Buffer(multiline=False)

        self.debug_buffer = DebugBuffer(self)

        self.log_handler = LogBuffer(self)
        self.log_buffer = self.log_handler.buffer_inst

        self.buffer_completer: Completer = None

        self.buffers = []
        self.active_buffer = self.debug_buffer

        self.bindings = SnoBinds(self)
        self.layout = SnoLayout(self)

        self._colorscheme = "vim"
        self._pygments_class = None
        self._style: Style = None

        self._show_line_numbers = True
        self._show_relative_numbers = True
        self._expand_tab = True
        self._tabstop = 4
        self._display_unprintable_characters = True
        self._use_system_clipboard = True
        self._use_nerd_fonts = False

        self._terminal = None
        self._color_depth = None

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

        self.app = Application(
            layout=self.layout.layout,
            style=self.style,
            clipboard=self.clipboard,
            key_bindings=self.bindings,
            full_screen=True,
            editing_mode=EditingMode.VI,
            mouse_support=True,
            color_depth=self._get_color_depth(),
        )

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
                "search": f"bg:{self.pygments_class.styles[String]} {self.pygments_class.highlight_color} underline",
                "selected": f"bg:{self.pygments_class.styles[String]} {self.pygments_class.highlight_color} underline",
                "completion-menu.completion.current": f"{self.pygments_class.highlight_color} underline",
                "lsp-message-text": self.pygments_class.styles[Error],
                "vertmenu.selected": f"bg:{self.pygments_class.highlight_color} {self.pygments_class.styles[String]} underline",
            }
        )

        self.style = merge_styles([_style, self._style_extra])

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
    def use_nerd_fonts(self) -> bool:
        return self._use_nerd_fonts

    @use_nerd_fonts.setter
    def use_nerd_fonts(self, value):
        self._use_nerd_fonts = bool(value)
        self.refresh_layout()

    @property
    def clipboard(self):
        return (
            PyperclipClipboard() if self._use_system_clipboard else InMemoryClipboard()
        )

    @property
    def terminal(self):
        if self._terminal is None:
            return [get_default_shell()]
        return shlex.split(self._terminal)

    @terminal.setter
    def terminal(self, value) -> None:
        self._terminal = value

    @property
    def color_depth(self):
        return self._get_color_depth()

    @color_depth.setter
    def color_depth(self, value):
        self._color_depth = value

    def _get_color_depth(self):
        if self._color_depth is None:
            return None
        if self._color_depth <= 0:
            return ColorDepth.MONOCHROME
        elif self._color_depth <= 1:
            return ColorDepth.DEPTH_1_BIT
        elif self._color_depth <= 4:
            return ColorDepth.DEPTH_4_BIT
        elif self._color_depth <= 8:
            return ColorDepth.DEPTH_8_BIT
        else:
            return ColorDepth.DEPTH_24_BIT

    def log(self, text: str) -> None:
        self.log_handler.write(text)
        self.focus_log_buffer()

    def clear_log(self) -> None:
        self.log_handler.clear()
        self.unfocus_log_buffer()

    def focus_log_buffer(self) -> None:
        self.app.layout.focus(self.log_buffer)
        self.app.vi_state.input_mode = InputMode.NAVIGATION

    def unfocus_log_buffer(self) -> None:
        self.app.layout.focus_last()
        self.app.vi_state.input_mode = InputMode.NAVIGATION

    def reset_buffers(self) -> None:
        if has_focus(self.command_buffer):
            self.leave_command_mode()
        if has_focus(self.log_buffer):
            self.clear_log()

    def add_buffer(self, buffer: SnooBuffer) -> None:
        if buffer.display_name in [b.display_name for b in self.buffers]:
            buffer.display_name = buffer.display_name_with_index
        if not self.buffers:
            self.buffers.append(buffer)
        else:
            index = self.active_buffer.index
            self.buffers.insert(index + 1, buffer)
        self.active_buffer = buffer
        self.refresh_layout()
        if buffer.read_only:
            self.log(get_string("read_only"))

    async def create_file_buffer(self, path: str, encoding: str = "utf-8") -> None:
        try:
            if not path:
                return
            for buffer in self.buffers:
                if buffer.path == os.path.abspath(path):
                    if not buffer.path == self.active_buffer.path:
                        self.select_buffer(buffer.index)
                        return
            buffer = FileBuffer(self, os.path.abspath(path), encoding)
            await buffer.load()
            self.add_buffer(buffer)
        except Exception as e:
            if isinstance(e, IsADirectoryError):
                self.log(str(e))

    def select_buffer(self, index):
        if isinstance(index, str):
            if index.endswith("*debug*"):
                for b in self.buffers:
                    if b.display_name.endswith("*debug*"):
                        index = b.index
                if isinstance(index, str):
                    self.debug_buffer.reindex()
                    self.buffers.append(self.debug_buffer)
                    index = self.debug_buffer.index
            else:
                pattern = re.compile(r"\[(\d+)\]")
                match = pattern.search(index)
                if match:
                    index = int(match.group(1))

        self.active_buffer = self.buffers[index]
        self.refresh_layout()

    async def save_current_buffer(self) -> None:
        if not await self.active_buffer.save():
            self.log(get_string("read_only"))
            return False
        return True

    async def save_all_buffers(self) -> None:
        for b in reversed(self.buffers):
            if not await b.save():
                break

    async def close_current_buffer(self, buffer=None, forced: bool = False) -> bool:
        if not buffer:
            buffer = self.active_buffer
        if buffer.saved or forced:
            if len(self.buffers) == 1:
                await self.buffers[0].close()
                self.layout.terminal.kill_terminal()
                get_app().exit()
                return True
            else:
                index = buffer.index
                buffer = self.buffers.pop(index)
                await buffer.close()
                self.active_buffer = self.buffers[index - 1]
                self.refresh_layout()
                return True
        else:
            if len(self.buffers) > 1:
                await self.select_buffer(buffer.index)
            self.log(get_string("not_saved"))
            return False

    async def close_all_buffers(self, forced: bool = False) -> bool:
        for b in reversed(self.buffers):
            if not await self.close_current_buffer(buffer=b, forced=forced):
                break

    def show_tree_menu(self):
        self.filters.tree_menu_toggle()
        self.app.layout.focus(self.layout.directory_tree)

    def close_tree_menu(self):
        self.filters.tree_menu_toggle()
        self.app.layout.focus(self.active_buffer.buffer_inst)

    def show_terminal(self):
        self.filters.terminal_toggle()
        self.app.layout.focus(self.layout.terminal)

    def close_terminal(self):
        self.filters.terminal_toggle()
        self.app.layout.focus(self.active_buffer.buffer_inst)

    def refresh_layout(self) -> None:
        if self.app:
            for buffer in self.buffers:
                buffer.reindex()
            self.app.invalidate()
            self.app.layout = self.layout.layout

    def _load_snorc(self) -> None:
        if os.path.isfile(self.home_dir / ".snorc"):
            with open(self.home_dir / ".snorc") as rc:
                with redirect_stdout(self.debug_buffer):
                    with redirect_stderr(self.debug_buffer):
                        xonsh.built_ins.XSH.builtins.execx(
                            rc.read(), glbs={"editor": self}
                        )

    async def _load_snorc_async(self) -> None:
        await run_in_executor_with_context(self._load_snorc)

    def execx(self, code) -> None:
        xonsh.built_ins.XSH.builtins.execx(code, glbs={"editor": self})

    async def aexecx(self, code) -> None:
        await run_in_executor_with_context(self.execx, code)
