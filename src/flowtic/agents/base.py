from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from flowtic.session import SessionManager
from flowtic.agents.tools import Tool, Tools
from litellm import completion, acompletion
from flowtic.communication import Callback

class AgentInterface(ABC):
    def __init__(
        self,
        agent_name: str,
        model_name: str,
        instructions: str | None = "You are a helpful assistant.",
        tools: Tools | None = None,
        tool_choice: str | None = None,
        session: Optional[SessionManager] = None,
        allow_user_input: bool = True,
        max_turns: int = -1,
        callbacks: Callback | None = None,
        temperature: float = 1
    ):
        self.agent_name = agent_name
        self.model_name = model_name
        self.instructions = instructions
        self.tools = tools
        self.tool_choice = tool_choice
        self.session = session
        self.allow_user_input = allow_user_input
        self.max_turns = max_turns
        self.callbacks = callbacks
        self.temperature = temperature

        if not self.session:
            self.session = SessionManager()
        
        assert self.allow_user_input == (self.callbacks is not None), "Callbacks should be provided if allow_user_input is True"

        if not self.callbacks:
            self.callbacks = Callback()
        
        if not self.allow_user_input:
            self.instructions += '\nYou are STRICTLY NOT allowed to communicate to user directly, contact to any other agents if you are allowed to.'
        
        if self.agent_name:
            self.instructions = f'\nYou are {self.agent_name}. ' + self.instructions

        self._register_session()
        self.session.add_sys_ins(self.name, instructions)
    
    @property
    def name(self) -> str:
        return self.agent_name
    
    def completion(self, **kwargs) -> Any:
        return completion(
                model=self.model_name,
                messages=self.session.get_buffer_memory(tag=self.name),
                tools=self.tools.get_definitions() if self.tools else None,
                tool_choice=self.tool_choice if self.tools else None,
                temperature=self.temperature,
                **kwargs
            )

    def acompletion(self, **kwargs) -> Any:
        return acompletion(
                model=self.model_name,
                messages=self.session.get_buffer_memory(tag=self.name),
                tools=self.tools.get_definitions() if self.tools else None,
                tool_choice=self.tool_choice if self.tools else None,
                temperature=self.temperature,
                **kwargs
            )
    
    def _register_session(self) -> None:
        self.session._register_buffer(self.name)
    
    def add_context(
        self,
        input: Optional[Dict[str, Any]] = None,
        assistant_output: Optional[Any] = None,
        tool_output: Optional[Dict[str, Any]] = None,
    ) -> None:
        if input:
            self.session.add_user_context(self.name, **input)
        elif assistant_output:
            self.session.add_assistant_context(self.name, assistant_output)
        elif tool_output:
            self.session.add_tool_context(self.name, **tool_output)
        else:
            raise ValueError("No input provided")
    
    def add_tool(self, tool: Tool) -> None:
        if not self.tools:
            self.tools = Tools([tool])
        else:
            self.tools.register_tool(tool)
