from typing import Dict, Callable, List

class Tool():
    def __init__(
        self,
        tool_definition: Dict,
        tool_execution: Callable,
    ) -> None:
        self.tool_definition = tool_definition
        self.tool_execution = tool_execution

        assert tool_definition['function']['name'] == tool_execution.__name__, "Tool name mismatch"

    def get_name(self) -> str:
        return self.tool_definition['function']['name']

class Tools():
    def __init__(
        self,
        tools: List[Tool]
    ):
        self.tools = tools
        self._map = None
        self._create_map()
    
    def _create_map(self):
        self._map = {tool.get_name(): tool.tool_execution for tool in self.tools}
    
    def get_callable(self, tool_name: str) -> Callable:
        if tool_name not in self._map:
            raise ValueError(f"Tool {tool_name} not found")
        return self._map[tool_name]
    
    def get_definitions(self) -> List[Dict]:
        return [tool.tool_definition for tool in self.tools]
    
    def register_tool(self, tool: Tool) -> None:
        self.tools.append(tool)
        self._create_map()