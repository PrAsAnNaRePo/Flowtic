from flowtic.agents import Agent
from flowtic.agents.tools import Tool, Tools
from flowtic.communication import CommunicationProtocol
from flowtic.communication import Callback
import os

os.environ["AZURE_API_KEY"] = ""
os.environ["AZURE_API_BASE"] = ""
os.environ["AZURE_API_VERSION"] = ""

class MyCallback(Callback):
    def on_user_loop(self, assistant_message: str):
        return input(assistant_message + ": ")

def main():
    product_manager = Agent(
        agent_name='product_manager',
        model_name='azure/gpt-4.1',
        instructions='You are a high level product manager who gets the requirement for the product and plans the product to developer to get work from him effectively.',
        tools=None,
        tool_choice=None,
        session=None,
        allow_user_input=True,
        max_turns=-1,
        callbacks=MyCallback(),
    )

    developer = Agent(
        agent_name='developer',
        model_name='azure/gpt-4.1',
        instructions='You are a developer who gets the plan from the product manager and implements it. you can get back to your product manager if you have any doubts.',
        tools=None,
        tool_choice=None,
        session=None,
        allow_user_input=False,
        max_turns=-1,
        callbacks=None,
    )

    protocol = CommunicationProtocol('product_manager<->developer', [product_manager, developer])

    protocol.execute(input="heyy!")

if __name__ == '__main__':
    main()
