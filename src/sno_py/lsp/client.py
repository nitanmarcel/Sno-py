import asyncio
import contextlib
import pathlib
import subprocess
from dataclasses import dataclass
from typing import AsyncGenerator, Coroutine, List, Optional, Type

import sansio_lsp_client as lsp
from pydantic import BaseModel, parse_obj_as
from sansio_lsp_client.io_handler import _make_request, _make_response
from sansio_lsp_client.structs import JSONDict, Request


class LanguageServerCrashed(Exception): ...


@dataclass
class NotificationHandler:
    of_type: BaseModel
    func: Coroutine


# CC: https://github.com/dsanders11/chromium-include-cleanup/blob/25ff1861ae8ce9cd0ebd4caa2a5c9c524def9b23/clangd_lsp.py#L60
class AsyncSendLspClient(lsp.Client):
    def _ensure_send_buf_is_queue(self):
        if not isinstance(self._send_buf, asyncio.Queue):
            self._send_buf: asyncio.Queue[bytes] = asyncio.Queue()

    def _send_request(self, method: str, params: Optional[JSONDict] = None) -> int:
        self._ensure_send_buf_is_queue()

        id = self._id_counter
        self._id_counter += 1

        self._send_buf.put_nowait(_make_request(method=method, params=params, id=id))
        self._unanswered_requests[id] = Request(id=id, method=method, params=params)
        return id

    def _send_notification(
        self, method: str, params: Optional[JSONDict] = None
    ) -> None:
        self._ensure_send_buf_is_queue()
        self._send_buf.put_nowait(_make_request(method=method, params=params))

    def _send_response(
        self,
        id: int,
        result: Optional[JSONDict] = None,
        error: Optional[JSONDict] = None,
    ) -> None:
        self._ensure_send_buf_is_queue()
        self._send_buf.put_nowait(_make_response(id=id, result=result, error=error))

    def _handle_request(self, request: lsp.Request) -> lsp.Event:
        # TODO - This is copied from sansio-lsp-client
        def parse_request(event_cls: Type[lsp.Event]) -> lsp.Event:
            if issubclass(event_cls, lsp.ServerRequest):
                event = parse_obj_as(event_cls, request.params)
                assert request.id is not None
                event._id = request.id
                event._client = self
                return event
            elif issubclass(event_cls, lsp.ServerNotification):
                return parse_obj_as(event_cls, request.params)
            else:
                raise TypeError(
                    "`event_cls` must be a subclass of ServerRequest"
                    " or ServerNotification"
                )

        return super()._handle_request(request)

    async def async_send(self) -> bytes:
        return await self._send_buf.get()


# Partially based on sansio-lsp-client/tests/test_actual_langservers.py
class LspClient:
    def __init__(self, root_path: str):
        self.root_path = pathlib.Path(root_path)
        self.lsp_client = AsyncSendLspClient(
            root_uri=pathlib.Path(root_path).as_uri(),
            trace="verbose",
        )

        self._process = None
        self._concurrent_tasks = None
        self._messages = []
        self._new_messages = asyncio.Queue()
        self._notification_queues = []
        self._process_gone = asyncio.Event()
        self._notification_handlers = []

        self._signature_triggers = []

    async def _send_stdin(self):
        try:
            while self._process:
                message = await self.lsp_client.async_send()
                self._process.stdin.write(message)
                await self._process.stdin.drain()
        except asyncio.CancelledError:
            pass

        self._process_gone.set()

    async def _process_stdout(self):
        try:
            while self._process:
                data = await self._process.stdout.read(1024)
                if data == b"":  # EOF
                    break

                # Parse the output and enqueue it
                for event in self.lsp_client.recv(data):
                    if isinstance(event, lsp.ServerNotification):
                        # If a notification comes in, tell anyone listening
                        for queue in self._notification_queues:
                            queue.put_nowait(event)
                    else:
                        self._new_messages.put_nowait(event)
                        self._try_default_reply(event)
        except asyncio.CancelledError:
            pass

        self._process_gone.set()

    async def _log_stderr(self):
        try:
            while self._process:
                line = await self._process.stderr.readline()
                if line == b"":  # EOF
                    break

                # Log the output for debugging purposes
                self.logger.debug(line.decode("utf8").rstrip())
        except asyncio.CancelledError:
            pass

        self._process_gone.set()

    async def start(self, cmd: str, args: List[str]):
        self._process = await asyncio.create_subprocess_exec(
            cmd,
            *args,
            cwd=self.root_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._concurrent_tasks = asyncio.gather(
            self._send_stdin(),
            self._process_stdout(),
            self._log_stderr(),
            return_exceptions=True,
        )

        initialized = await self._wait_for_message_of_type(lsp.Initialized)
        self._signature_triggers = initialized.capabilities.get(
            "signatureHelpProvider", {}
        ).get("triggerCharacters", [])

    def _try_default_reply(self, msg):
        if isinstance(
            msg,
            (
                lsp.ShowMessageRequest,
                lsp.WorkDoneProgressCreate,
                lsp.RegisterCapabilityRequest,
                lsp.ConfigurationRequest,
            ),
        ):
            msg.reply()

    async def _wait_for_message_of_type(self, message_type, timeout=5):
        for message in self._messages:
            if isinstance(message, message_type):
                self._messages.remove(message)
                return message

        while True:
            message = await asyncio.wait_for(self._new_messages.get(), timeout=timeout)
            if isinstance(message, message_type):
                return message
            else:
                self._messages.append(message)

    async def _wrap_coro(self, coro):
        process_gone_task = asyncio.create_task(self._process_gone.wait())
        task = asyncio.create_task(coro)
        done, _ = await asyncio.wait(
            {task, process_gone_task}, return_when=asyncio.FIRST_COMPLETED
        )

        if process_gone_task in done:
            task.cancel()
            raise LanguageServerCrashed()
        else:
            process_gone_task.cancel()

        return task.result()

    @contextlib.asynccontextmanager
    async def _listen_for_notifications(self, cancellation_token=None):
        queue = asyncio.Queue()
        if cancellation_token is None:
            cancellation_token = asyncio.Event()

        async def get_notifications():
            cancellation_token_task = asyncio.create_task(cancellation_token.wait())

            try:
                while not cancellation_token.is_set():
                    queue_task = asyncio.create_task(self._wrap_coro(queue.get()))
                    done, _ = await asyncio.wait(
                        {queue_task, cancellation_token_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    if cancellation_token_task in done:
                        queue_task.cancel()
                        break
                    else:
                        yield queue_task.result()
            finally:
                cancellation_token_task.cancel()

        self._notification_queues.append(queue)
        yield get_notifications()
        cancellation_token.set()
        self._notification_queues.remove(queue)

    async def listen_for_notifications(self, cancellation_token: asyncio.Event):
        async with self._listen_for_notifications(
            cancellation_token=cancellation_token
        ) as notifier:
            async for notification in notifier:
                for handler in self._notification_handlers:
                    if isinstance(notification, handler.of_type):
                        await handler.func(notification)

    def add_notification_handler(self, of_type: BaseModel, func: Coroutine):
        self._notification_handlers.append(
            NotificationHandler(of_type=of_type, func=func)
        )

    def remove_notification_handler(self, of_type: BaseModel, func: Coroutine):
        for handler in self._notification_handlers:
            if handler.of_type == of_type and handler.func == func:
                self._notification_handlers.remove(handler)
                break

    @staticmethod
    def validate_config(root_path: pathlib.Path):
        # TODO - Check for a valid config with IncludeCleaner setup
        return True

    def open_document(
        self, language_id: str, file_path: str, file_contents: str
    ) -> lsp.TextDocumentItem:
        document = lsp.TextDocumentItem(
            uri=pathlib.Path(file_path).as_uri(),
            languageId=language_id,
            text=file_contents,
            version=1,
        )

        self.lsp_client.did_open(document)

        return document

    def close_document(self, file_path: str):
        self.lsp_client.did_close(
            lsp.TextDocumentIdentifier(
                uri=pathlib.Path(file_path).as_uri(),
            )
        )

    def change_document(
        self,
        file_path: str,
        version: int,
        text: str,
        want_diagnostics: Optional[bool] = None,
    ):
        text_document = lsp.VersionedTextDocumentIdentifier(
            uri=pathlib.Path(file_path).as_uri(),
            version=version,
        )
        content_changes = [lsp.TextDocumentContentChangeEvent(text=text)]

        # NOTE - The following is copied from sansio-lsp-client to add the wantDiagnostics property
        assert self.lsp_client._state == lsp.ClientState.NORMAL

        params = {
            "textDocument": text_document.dict(),
            "contentChanges": [evt.dict() for evt in content_changes],
        }

        if want_diagnostics is not None:
            params["wantDiagnostics"] = want_diagnostics

        self.lsp_client._send_notification(
            method="textDocument/didChange",
            params=params,
        )

    def save_document(self, document_path: str):
        self.lsp_client.did_save(
            lsp.TextDocumentIdentifier(
                uri=pathlib.Path(document_path).as_uri(),
            )
        )

    async def request_completion(
        self, file_path: str, line: int, character: int
    ) -> AsyncGenerator[lsp.CompletionItem, None]:
        self.lsp_client.completion(
            text_document_position=lsp.TextDocumentPosition(
                textDocument=lsp.TextDocumentIdentifier(
                    uri=pathlib.Path(file_path).as_uri()
                ),
                position=lsp.Position(line=line, character=character),
            ),
            context=lsp.CompletionContext(
                triggerKind=lsp.CompletionTriggerKind.INVOKED
            ),
        )

        if (
            completion_list := (
                await self._wait_for_message_of_type(lsp.Completion)
            ).completion_list
        ) is not None:
            for item in completion_list.items:
                yield item

    async def request_signature(self, file_path: str, line: int, character: int):
        self.lsp_client.signatureHelp(
            text_document_position=lsp.TextDocumentPosition(
                textDocument=lsp.TextDocumentIdentifier(
                    uri=pathlib.Path(file_path).as_uri()
                ),
                position=lsp.Position(line=line, character=character),
            ),
        )

        signature = await self._wait_for_message_of_type(lsp.SignatureHelp)
        return signature.get_hint_str()

    @property
    def signature_triggers(self):
        return self._signature_triggers

    async def exit(self):
        if self._process:
            try:
                if self._process.returncode is None and not self._process_gone.is_set():
                    self.lsp_client.shutdown()
                    shutdown_task = asyncio.create_task(
                        self._wait_for_message_of_type(lsp.Shutdown, timeout=None)
                    )
                    done, _ = await asyncio.wait(
                        {shutdown_task, self._concurrent_tasks},
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if shutdown_task in done:
                        self.lsp_client.exit()
                    else:
                        shutdown_task.cancel()
            except Exception:
                pass
            finally:
                # Cleanup the subprocess
                try:
                    self._process.terminate()
                except ProcessLookupError:
                    pass
                await self._process.wait()
                self._process = None

        try:
            self._concurrent_tasks.cancel()
            await self._concurrent_tasks
        except asyncio.CancelledError:
            pass
        self._concurrent_tasks = None
