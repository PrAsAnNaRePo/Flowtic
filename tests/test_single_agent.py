from flowtic.agents import Agent
from flowtic.agents.tools import Tool, Tools
from flowtic.communication import Callback
import os

os.environ["AZURE_API_KEY"] = ""
os.environ["AZURE_API_BASE"] = ""
os.environ["AZURE_API_VERSION"] = ""

class MyCallback(Callback):
    def on_user_loop(self, assistant_message: str):
        return input(assistant_message + ": ")

def calculator_tool(expression: str):
    return str(eval(expression)), None

calculatorl = Tool(
    tool_definition={
        "type": "function",
        'function': {
            'name': 'calculator_tool',
            'description': 'Calculate the result of a mathematical expression',
            'parameters': {
                'type': 'object',
                'properties': {
                    'expression': {
                        'type': 'string',
                        'description': 'The mathematical expression to evaluate'
                    }
                },
                'required': ['expression']
            }
        }
    },
    tool_execution=calculator_tool
)

def main():
    agent = Agent(
        agent_name='agent',
        model_name='azure/gpt-4.1',
        instructions='You are a helpful assistant.',
        tools=Tools([calculatorl]),
        tool_choice='auto',
        session=None,
        allow_user_input=False,
        max_turns=-1,
        callbacks=MyCallback(),
    )

    print(agent('heyy!'))

if __name__ == '__main__':
    main()
