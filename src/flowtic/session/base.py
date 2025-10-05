from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

class SessionInterface(ABC):
    def __init__(self, ctx_size: int = 4):
        self._buffer_memory = dict()
        self._ctx_size = ctx_size

    @property
    def ctx_size(self) -> int:
        return self._ctx_size
    
    @ctx_size.setter
    def ctx_size(self, value: int):
        self._ctx_size = value
    
    def get_buffer_memory(self, tag: str) -> List:
        return self._buffer_memory[tag]
    
    def add_sys_ins(self, tag: str, instruction: str):
        self._buffer_memory[tag].append(
            {
                'role': 'system',
                'content': instruction
            }
        )

    @abstractmethod
    def add_user_context(self, tag: str, text: Optional[str] = None, images: Optional[List] = None): ...
    
    @abstractmethod
    def add_assistant_context(self, tag: str, ass_out: Any): ...
    
    @abstractmethod
    def add_tool_context(self, tag: str, text: Optional[str] = None, images: Optional[List] = None): ...

    def _register_buffer(self, tag: str):
        if tag not in self._buffer_memory:
            self._buffer_memory[tag] = []
        else:
            raise ValueError(f"Tag {tag} already exists")
