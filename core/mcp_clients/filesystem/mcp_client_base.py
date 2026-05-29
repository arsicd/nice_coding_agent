from abc import ABC, abstractmethod


class FilesystemMcpClient(ABC):
    @abstractmethod
    async def get_file_text(self, path: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def list_directory_tree(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def replace_text_in_file(
        self, path: str, old_text: str, new_text: str
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def create_file(self, path: str, content: str) -> str:
        raise NotImplementedError
