from typing import Union, TYPE_CHECKING
from asyncio import get_event_loop
from functools import partial

from prompt_toolkit.application import in_terminal
from prompt_toolkit.application.application import _do_wait_for_enter
from prompt_toolkit.eventloop import run_in_executor_with_context

if TYPE_CHECKING:
    from xonsh.built_ins import XonshSession

from sno_py.di import container


class Xsh:
    def __init__(self) -> None:
        self.xsh: Union["XonshSession", None] = None
        self.loop = get_event_loop()

    async def load_snorc(self, content: str) -> None:
        await self._ensure_xnosh_loaded()

        await self.loop.run_in_executor(
            None,
            partial(
                self.xsh.builtins.execx,
                (content),
                glbs={"container": container},
            ),
        )

    async def exec(self, code: str, wait_for_enter: bool = True) -> None:
        await self._ensure_xnosh_loaded()

        async with in_terminal():
            await run_in_executor_with_context(
                partial(self.xsh.builtins.execx, code, glbs={"container": container})
            )
            if wait_for_enter:
                await _do_wait_for_enter("Press ENTER to continue...")

    async def _ensure_xnosh_loaded(self) -> None:
        import xonsh.built_ins

        xonsh.built_ins.resetting_signal_handle = lambda sig, f: None

        import xonsh.execer
        import xonsh.imphooks

        execer = xonsh.execer.Execer()

        await self.loop.run_in_executor(
            None, partial(xonsh.built_ins.XSH.load, execer=execer, inherit_env=True)
        )

        await self.loop.run_in_executor(
            None, partial(xonsh.imphooks.install_import_hooks, execer=execer)
        )

        self.xsh = xonsh.built_ins.XSH
