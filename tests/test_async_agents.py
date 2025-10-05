from flowtic.agents import AsyncAgent
from flowtic.agents.tools import Tool, Tools
from flowtic.communication import CommunicationProtocol
from flowtic.communication import Callback
import subprocess
import os

os.environ["AZURE_API_KEY"] = ""
os.environ["AZURE_API_BASE"] = ""
os.environ["AZURE_API_VERSION"] = ""


def terminal_tool(command: str):
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        output = completed.stdout + completed.stderr
    except Exception as exc:
        output = f"[terminal_tool error] {exc}"

    return output, None

terminal_tool_call = Tool(
    tool_definition={
        "type": "function",
        'function': {
            'name': 'terminal_tool',
            'description': 'Execute a terminal command',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {
                        'type': 'string',
                        'description': 'The command to execute'
                    }
                },
                'required': ['command']
            }
        }
    },
    tool_execution=terminal_tool
)


class MyCallback(Callback):
    def on_user_loop(self, agent_name: str, assistant_message: str):
        return input(agent_name + ": " + assistant_message + ": ")
    
    def on_tool_call(self, agent_name: str, fn_name: str, arguments: dict):
        print(f"{agent_name} ===> {fn_name}")

async def main():
    requirement_manager = AsyncAgent(
        agent_name='requirement_manager',
        model_name='azure/gpt-4.1',   # <- your_model_here
        instructions='''
        you are a requirement analyst who gather very detailed requirements to build the whole project.
clarify with user to get the full picture of the project they asking for.
if your're enough confidence with the requirement you can directly send it to product manager with a clear report
you do not have to generate code''',
        tools=None,
        tool_choice=None,
        session=None,
        allow_user_input=True,
        max_turns=-1,
        callbacks=MyCallback(),
    )

    product_manager = AsyncAgent(
        agent_name='product_manager',
        model_name='azure/gpt-4.1',   # <- your_model_here
        instructions='You are a high level product manager who gets the requirement report from requirement manager and validate with requirement manager and finally plan out the entire product as feature list and get the work done from developer by splitting the work.',
        tools=None,
        tool_choice="auto",
        session=None,
        allow_user_input=False,
        max_turns=-1,
        callbacks=None,
    )

    developer = AsyncAgent(
        agent_name='developer',
        model_name='azure/gpt-5-chat',   # <- your_model_here
        instructions='You are a developer who gets the plan from the product manager and implements it. you can get back to your product manager if you have any doubts.',
        tools=Tools([terminal_tool_call]),
        tool_choice="auto",
        session=None,
        allow_user_input=False,
        max_turns=-1,
        callbacks=None,
    )

    protocol = CommunicationProtocol('requirement_manager<->product_manager, product_manager->developer', [requirement_manager, product_manager, developer], async_run_type=True)

    await protocol.asyn_execute(input="heyy!")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

