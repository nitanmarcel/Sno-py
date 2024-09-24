from asyncio.subprocess import Process
from sansio_lsp_client.events import (
    Completion,
    Initialized,
)
from typing import (
    Optional,
    Type,
    Union,
)


class LanguageClient:
    def __init__(self, process: Process, root_path: Optional[str] = ...) -> None: ...
    async def _queue_send(self) -> None: ...
    async def _read_loop(self): ...
    async def _read_received(self) -> None: ...
    async def _send_loop(self): ...
    def _try_default_reply(
        self,
        ev: Union[Completion, Initialized]
    ) -> None: ...
    async def completion(
        self,
        text: str,
        file_path: str,
        line: int,
        character: int
    ) -> Completion: ...
    async def wait_for_message(
        self,
        of_type: Union[Type[Completion], Type[Initialized]],
        timeout: int = ...
    ) -> Union[Completion, Initialized]: ...
