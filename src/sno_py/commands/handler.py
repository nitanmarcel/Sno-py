import inspect
import re
import shlex
from functools import wraps
from typing import TYPE_CHECKING, Callable, List, Union

from attrs import fields
from prompt_toolkit.application import get_app
from prompt_toolkit.completion import Completer
from prompt_toolkit.output.color_depth import ColorDepth

from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.commands.completer import CompleteHandler
    from sno_py.config import Config
    from sno_py.editor import Editor
    from sno_py.style import EditorStyle
    from sno_py.xsh import Xsh


class CommandHandler:
    def __init__(self) -> None:
        self._handlers: dict = {}
        self._completers: dict = {}
        self._complete_handler: "CompleteHandler" = container["CompleteHandler"]
        self._command_list: list = []
        self._init_defaults()

    async def run(self, command_input) -> None:
        if not command_input:
            return

        commands = self._parse_command(command_input)
        editor = container["Editor"]

        for cmd in commands:
            match = re.match(r"(\w+!?|[!@#$%^&*()/:;])(.*)", cmd.strip())
            if not match:
                editor.show_message(f"Error: Invalid command format '{cmd}'")
                continue

            cmd_name, args_str = match.groups()
            force = False

            if cmd_name.endswith("!") and cmd_name not in ["!", "!!"]:
                force = True
                cmd_name = cmd_name[:-1]

            if cmd_name in self._handlers:
                handler = self._handlers[cmd_name]
                args = self._parse_vim_args(
                    args_str, expects_file=handler["expects_file"]
                )

                if handler["allow_force"]:
                    args["force"] = force
                elif force:
                    args["!"] = True

                result = handler["func"](**args)
                if inspect.isawaitable(result):
                    await result
            else:
                editor.show_message(f"Error: Command '{cmd_name}' not found")

    def _parse_command(self, command_input) -> list | list[str]:
        if isinstance(command_input, list):
            return command_input
        elif isinstance(command_input, str):
            return [command_input]
        else:
            raise ValueError("Invalid command input type")

    def _parse_vim_args(self, args_str, expects_file=False) -> dict:
        args = {}

        try:
            parts = shlex.split(args_str)
        except ValueError:
            parts = args_str.split()

        arg_index = 0
        for i, part in enumerate(parts):
            if "=" in part and not part.startswith("="):
                key, value = part.split("=", 1)
                args[key] = value.strip("\"'")

            elif part.startswith("+") and part[1:].isdigit():
                args["line"] = part[1:]

            elif i == 0 and expects_file and not part.startswith("-"):
                args["file"] = part

            elif part.startswith("-"):
                if part.startswith("--"):
                    args[part[2:]] = True
                else:
                    for flag in part[1:]:
                        args[flag] = True

            else:
                args[f"arg{arg_index}"] = part
                arg_index += 1

        return args

    def cmd(
        self,
        *names,
        allow_force=False,
        complete: Union[str, List[str], Callable, None] = None,
        expects_file=False,
    ):
        def decorator(func):
            @wraps(func)
            def wrapper(**kwargs):
                sig = inspect.signature(func)
                try:
                    bound_args = sig.bind(**kwargs)
                    bound_args.apply_defaults()
                    return func(**bound_args.arguments)
                except TypeError as e:
                    error_msg = str(e)
                    if "missing a required argument" in error_msg:
                        msg = f"Error: Too few arguments for command '{names[0]}'"
                    elif "got an unexpected keyword argument" in error_msg:
                        msg = f"Error: Too many arguments for command '{names[0]}'"
                    else:
                        msg = f"Error executing command '{names[0]}': {error_msg}"

                    editor = container["Editor"]
                    editor.show_message(msg)
                    return None

            for name in names:
                self._handlers[name] = {
                    "func": wrapper,
                    "allow_force": allow_force,
                    "expects_file": expects_file,
                }
                self._command_list.append(name)

                if complete is not None:
                    if isinstance(complete, str):
                        self._completers[name] = self._complete_handler.get_completer(
                            complete
                        )
                    elif isinstance(complete, list) or callable(complete):
                        self._completers[name] = self._complete_handler.words(complete)
                    else:
                        raise ValueError(f"Invalid completion type for command {name}")

            return wrapper

        return decorator

    def command_exists(self, name: str) -> bool:
        return name in self._handlers

    def get_completer(self, cmd_name: str) -> Completer | None:
        if cmd_name in self._completers:
            return self._completers[cmd_name]
        return self._complete_handler.get_completer("command")

    def get_command_list(self) -> List[str]:
        return self._command_list

    def _init_defaults(self) -> None:
        config: "Config" = container["Config"]
        editor: "Editor" = container["Editor"]
        style: "EditorStyle" = container["EditorStyle"]
        xsh: "Xsh" = container["Xsh"]

        @self.cmd("colorscheme", complete=style.get_colorschemes)
        async def _colorscheme(arg0: str) -> None:
            config.colorscheme = arg0

        @self.cmd("echo")
        async def _echo(**kwargs) -> None:
            editor.show_message(" ".join(str(value) for value in kwargs.values()))

        @self.cmd("e", "edit", complete="file", expects_file=True)
        async def _edit_file(file: str = None, line: str = None, **kwargs):
            cursor_pos = 0
            if line:
                try:
                    cursor_pos = int(line) - 1
                except ValueError:
                    editor.show_message("Invalid line number")
                    return

            if file:
                buffer = await editor.wm.create_buffer(file, cursor_pos=cursor_pos)
                editor.wm.active_window.add_buffer(buffer)
                editor.wm.active_window.switch_to_buffer(buffer)
            elif editor.wm.active_window.active_buffer:
                current_buffer = editor.wm.active_window.active_buffer
                current_buffer.buffer.cursor_position = (
                    current_buffer.buffer.document.translate_row_col_to_index(
                        cursor_pos, 0
                    )
                )
            else:
                editor.show_message("No file specified and no active buffer")
                return

        async def _split_window(vertical: bool = False) -> None:
            await editor.wm.split(editor.wm.active_window, is_horizontal=not vertical)

        @self.cmd("vsplit")
        async def _vsplit_window() -> None:
            await editor.wm.split(is_horizontal=False)

        @self.cmd("hsplit")
        async def _hsplit_window() -> None:
            await editor.wm.split(is_horizontal=True)

        @self.cmd("w", "write")
        async def _write_buffer(**kwargs):
            if not editor.wm.active_window or not editor.wm.active_window.active_buffer:
                editor.show_message("No active buffer to write")
                return
            await editor.wm.active_window.active_buffer.write()
            editor.show_message(
                f"Wrote {editor.wm.active_window.active_buffer.get_display_name()}"
            )

        @self.cmd("wa", "wall")
        async def _write_all(**kwargs):
            buffers_written = 0
            for window in editor.wm.walk_windows():
                for buffer in window.buffers:
                    await buffer.write()
                    buffers_written += 1
            editor.show_message(f"Wrote {buffers_written} buffer(s)")

        @self.cmd("q", "quit", allow_force=True)
        async def _quit(force: bool = False, **kwargs):
            if not editor.wm.active_window:
                editor.show_message("No active window")
                return

            active_window = editor.wm.active_window
            active_buffer = active_window.active_buffer

            if not active_buffer:
                await editor.wm.close_window(active_window)
            else:
                if active_buffer.changed and not force:
                    editor.show_message(
                        f"No write since last change for buffer {active_buffer.get_display_name()} (add ! to override)"
                    )
                    return

                active_window.buffers.remove(active_buffer)

                if active_window.buffers:
                    active_window.switch_to_buffer(active_window.buffers[0])
                else:
                    await editor.wm.close_window(active_window)

            if not editor.wm.root:
                get_app().exit()
            elif not editor.wm.active_window:
                editor.wm.active_window = editor.wm._find_next_window(editor.wm.root)
                if not editor.wm.active_window:
                    get_app().exit()

        @self.cmd("qa", "qall", allow_force=True)
        async def _quit_all(force: bool = False, **kwargs):
            windows_to_close = list(editor.wm.walk_windows())
            unsaved_buffers = []

            if not force:
                for window in windows_to_close:
                    for buffer in window.buffers:
                        if buffer.changed:
                            unsaved_buffers.append(buffer)

                if unsaved_buffers:
                    editor.show_message(
                        "No write since last change (add ! to override)"
                    )
                    editor.wm.active_window.switch_to_buffer(unsaved_buffers[0])
                    return

            for window in windows_to_close:
                await editor.wm.close_window(window)

            get_app().exit()

        @self.cmd("wq", "x")
        async def _write_and_quit(**kwargs):
            if not editor.wm.active_window or not editor.wm.active_window.active_buffer:
                editor.show_message("No active buffer to write and quit")
                return
            await editor.wm.active_window.active_buffer.write()
            await _quit(force=True, **kwargs)

        @self.cmd("bn", "bnext")
        async def _next_buffer(**kwargs):
            if not editor.wm.active_window:
                editor.show_message("No active window")
                return
            current_index = editor.wm.active_window.get_active_buffer_index()
            next_index = (
                current_index + 1
            ) % editor.wm.active_window.get_buffer_count()
            editor.wm.active_window.select_buffer_by_index(next_index)

        @self.cmd("bp", "bprevious")
        async def _previous_buffer(**kwargs):
            if not editor.wm.active_window:
                editor.show_message("No active window")
                return
            current_index = editor.wm.active_window.get_active_buffer_index()
            prev_index = (
                current_index - 1
            ) % editor.wm.active_window.get_buffer_count()
            editor.wm.active_window.select_buffer_by_index(prev_index)

        @self.cmd("bd", "bdelete", allow_force=True)
        async def _delete_buffer(force: bool = False, **kwargs):
            if not editor.wm.active_window or not editor.wm.active_window.active_buffer:
                editor.show_message("No active buffer to delete")
                return
            active_buffer = editor.wm.active_window.active_buffer
            if active_buffer.changed and not force:
                editor.show_message(
                    f"No write since last change for buffer {active_buffer.get_display_name()} (add ! to override)"
                )
                return
            editor.wm.active_window.buffers.remove(active_buffer)
            if editor.wm.active_window.buffers:
                editor.wm.active_window.switch_to_buffer(
                    editor.wm.active_window.buffers[0]
                )
            else:
                await editor.wm.close_window(editor.wm.active_window)

        @self.cmd("ls", "buffers")
        async def _list_buffers(**kwargs):
            buffer_list = []
            for window in editor.wm.walk_windows():
                for buffer in window.walk_buffers():
                    buffer_list.append(
                        f"{buffer.buffer_id}: {buffer.get_display_name()}"
                    )
            editor.show_message("\n".join(buffer_list))

        @self.cmd("sp", "split")
        async def _split_window(**kwargs):
            await editor.wm.split(editor.wm.active_window, is_horizontal=True)

        @self.cmd("only")
        async def _only_window(**kwargs):
            if not editor.wm.active_window:
                editor.show_message("No active window")
                return
            windows_to_close = [
                w for w in editor.wm.walk_windows() if w != editor.wm.active_window
            ]
            for window in windows_to_close:
                await editor.wm.close_window(window)

        @self.cmd("set", complete="config")
        async def _set_option(arg0: str = None, arg1: str = None, **kwargs):
            config_fields = {
                field.name: field
                for field in fields(config.__class__)
                if field.name != "colorscheme"
            }

            if not arg0:
                for name, field in config_fields.items():
                    value = getattr(config, name)
                    editor.show_message(f"{name}={value}")
                return

            if arg0 not in config_fields:
                editor.show_message(f"Unknown option: {arg0}")
                return

            if arg1 is None:
                current_value = getattr(config, arg0)
                editor.show_message(f"{arg0}={current_value}")
            else:
                field = config_fields[arg0]
                try:
                    if field.type is bool:
                        new_value = arg1.lower() in ("true", "yes", "on", "1")
                    elif field.type is int:
                        new_value = int(arg1)
                    elif field.type is str:
                        new_value = arg1
                    elif field.type is ColorDepth:
                        new_value = int(arg1)
                    else:
                        raise ValueError(f"Unsupported type for option {arg0}")

                    field.validator(config.__class__, field, new_value)

                    setattr(config, arg0, new_value)
                    editor.show_message(f"Set {arg0}={getattr(config, arg0)}")
                except ValueError as e:
                    editor.show_message(f"Invalid value for {arg0}: {str(e)}")

        @self.cmd("wn", "wnext")
        async def _next_window(**kwargs):
            editor.wm.focus_next_window()

        @self.cmd("wp", "wprevious")
        async def _previous_window(**kwargs):
            editor.wm.focus_previous_window()

        @self.cmd("!", complete="system")
        async def _exec(**kwargs) -> None:
            code = " ".join(kwargs["kwargs"].values())
            await xsh.exec(code)
