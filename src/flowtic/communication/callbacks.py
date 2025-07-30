from typing import Dict, Any

class Callback:
    def __init__(self) -> None:
        pass

    def on_user_loop(self, assistant_message: str):
        raise NotImplementedError

    def on_tool_call(self, fn_name: str, arguments: Dict[str, Any]):
        print('Tool Call: ', fn_name, arguments)