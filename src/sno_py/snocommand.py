import ast
import inspect

from prompt_toolkit.completion import PathCompleter, WordCompleter
from prompt_toolkit.contrib.regular_languages.compiler import compile
from prompt_toolkit.contrib.regular_languages.completion import \
    GrammarCompleter

from sno_py import redirect

@redirect.debug_stderr
@redirect.debug_stdout
def q(editor, *args, **kwargs):
    if "force" in kwargs:
        return editor.close_current_buffer(forced=True)
    return editor.close_current_buffer()


@redirect.debug_stderr
@redirect.debug_stdout
async def qa(editor, *args, **kwargs):
    if "force" in kwargs:
        return await editor.close_all_buffers(forced=True)
    return await editor.close_all_buffers()


@redirect.debug_stderr
@redirect.debug_stdout
async def w(editor, *args, **kwargs) -> None:
    await editor.save_current_buffer()


@redirect.debug_stderr
@redirect.debug_stdout
async def wa(editor, *args, **kwargs) -> None:
    await editor.save_all_buffers()


@redirect.debug_stderr
@redirect.debug_stdout
async def o(editor, *args, **kwargs) -> None:
    del kwargs["_raw"]
    for arg in args:
        await editor.create_file_buffer(arg, **kwargs)


@redirect.debug_stderr
@redirect.debug_stdout
def o_completion_handler(editor, args: list):
    return GrammarCompleter(
        compile("o\s+(?P<path>\S+)"),
        {
            "path": PathCompleter(expanduser=True)
        }
    )


@redirect.debug_stderr
@redirect.debug_stdout
async def buffer(editor, *args, **kwargs) -> None:
    if (args):
        await editor.select_buffer(display_name=args[0])


@redirect.debug_stderr
@redirect.debug_stdout
def buffer_completion_handler(editor, args: list):
    return WordCompleter([b.display_name for b in editor.buffers])

@redirect.log_stderr
@redirect.log_stdout
async def execx(editor, *args, **kwargs) -> None:
    await editor.aexecx(kwargs["_raw"])
    
class SnoCommand:
    def __init__(self, editor) -> None:
        self._editor = editor
        self._handlers = {}
        self._completion_handlers = {}

        self.completer = self.default_completer

        self._create_defaults()

    async def run(self, command_input) -> str:
        if not command_input:
            return

        commands = self._parse_command(command_input)

        for cmd in commands:
            split = cmd.split(None, 1)
            args = []
            kwargs = {}
            if len(split) > 1:
                cmd, rest = split
                args, kwargs = self._parse_args_kwargs(rest)
            if cmd.endswith("!") and len(cmd) > 1:
                kwargs["force"] = True
                cmd = cmd[:-1]
            if cmd in self._handlers:
                kwargs["_raw"] = split[-1] if len(args) > 0 else ""
                func = self._handlers[cmd]
                if isinstance(func, list):
                    for f in func:
                        result = f(self._editor, *args, **kwargs)
                        if inspect.isawaitable(result):
                            await result
                else:
                    result = func(self._editor, *args, **kwargs)
                    if inspect.isawaitable(result):
                        await result

    def _parse_command(self, command_input):
        if isinstance(command_input, list):
            return command_input
        elif isinstance(command_input, str):
            return [command_input]
        else:
            raise ValueError("Invalid command input type")

    def _create_defaults(self) -> None:
        self.add_command_handler(q, "q")
        self.add_command_handler(qa, "qa")
        self.add_command_handler(w, "w")
        self.add_command_handler(wa, "wa")
        self.add_command_handler([w, q], "wq")
        self.add_command_handler([wa, qa], "wqa")
        self.add_command_handler(
            o, "o", completion_handler=o_completion_handler)
        self.add_command_handler(
            buffer, "buffer", completion_handler=buffer_completion_handler)
        self.add_command_handler(execx, "!")
        
    def add_command_handler(self, func, name: str, completion_handler=None) -> None:
        if isinstance(name, list):
            for n in name:
                self._handlers[n] = func
                if completion_handler:
                    self._completion_handlers[n] = completion_handler
        else:
            self._handlers[name] = func
            if completion_handler:
                self._completion_handlers[name] = completion_handler

    def _parse_args_kwargs(self, input_str):
        args = []
        kwargs = {}
        parts = input_str.split()

        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                try:
                    kwargs[key] = ast.literal_eval(value)
                except (SyntaxError, ValueError):
                    kwargs[key] = value
            else:
                args.append(part)

        return args, kwargs

    def command_exists(self, name: str) -> bool:
        return name in self._handlers

    def get_completion_handler(self, name: str):
        return self._completion_handlers.get(name)

    def get_completer_instance(self) -> None:
        pass

    def process_command_completion(self, buffer) -> None:
        text = buffer.text
        split = text.split(None, 1)
        completer = None
        if len(split) > 1 or text.endswith(" "):
            if text.strip():
                completer_handler = self.get_completion_handler(split[0])
                if completer_handler:
                    completer = completer_handler(
                        self._editor, split if len(split) > 1 else [])
            else:
                completer = None
        else:
            completer = self.default_completer

        if completer != self.completer:
            self.completer = completer
        self._editor.command_buffer.completer = completer

    @property
    def default_completer(self):
        return WordCompleter(
            words=self._handlers.keys()
        )
