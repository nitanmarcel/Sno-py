from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

from sno_py.lsp.client import LspClient
import sansio_lsp_client as lsp

import os

@dataclass
class ServerConfig:
    language_id: str
    extensions: List[str]
    command: str
    args: List[str]

@dataclass
class RunningServer:
    extensions: List[str]
    client: LspClient

class LanguageClientManager:
    def __init__(self) -> None:
        self._servers: List[ServerConfig] = []
        self._running: List[RunningServer] = []
        
    def add_server(self, language_id: str, extensions: List[str], command: str, args: List[str]):
        self._servers.append(ServerConfig(language_id=language_id, extensions=extensions, command=command, args=args))
    
    async def get_client(self, file_path: str, root_path: str) -> Optional[LspClient]:
        config = self.get_server_config(file_path)
        if not config:
            return None
        for server in self._running:
            if server.extensions == config.extensions:
                return server.client
        client = LspClient(root_path)
        await client.start(config.command, config.args)
        self._running.append(RunningServer(extensions=config.extensions, client=client))
        return client
    
    def get_client_if_exists(self, file_path: str) -> LspClient:
        config = self.get_server_config(file_path)
        if not config:
            return None
        for server in self._running:
            if server.extensions == config.extensions:
                return server.client
        
    def get_server_config(self, file_path) -> Optional[ServerConfig]:
        ext = self.get_extension_from_file_path(file_path)
        for config in self._servers:
            if ext in config.extensions:
                return config
        return None
    
    @staticmethod
    def get_extension_from_file_path(file_path):
        _, ext = os.path.splitext(file_path)
        return ext
    
    async def _process_notifications(self, client: LspClient):
        async with client.listen_for_notifications() as listener:
            for notification in listener:
                print(notification)
