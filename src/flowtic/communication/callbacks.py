from typing import Dict, Any

class Callback:
    def __init__(self) -> None:
        pass

    def on_user_loop(self, agent_name: str, assistant_message: str):
        raise NotImplementedError

    def on_tool_call(self, agent_name: str, fn_name: str, arguments: Dict[str, Any]):
        print(f"{agent_name} ===> {fn_name}")