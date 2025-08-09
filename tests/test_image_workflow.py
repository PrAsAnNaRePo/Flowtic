from flowtic.agents import Agent
from flowtic.agents.tools import Tool, Tools
from flowtic.communication import CommunicationProtocol
from flowtic.communication import Callback
import os
import base64
from PIL import Image, ImageDraw
from io import BytesIO

def read_image_from_file(file_path: str):
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}", None
        
        with open(file_path, 'rb') as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
        return f"Successfully read image from {file_path}", [base64_image]
    except Exception as e:
        return f"Error reading image: {str(e)}", None

read_image_tool = Tool(
    tool_definition={
        "type": "function",
        "function": {
            "name": "read_image_from_file",
            "description": "Read an image from a file path and return it",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the image file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    tool_execution=read_image_from_file
)

class MyCallback(Callback):
    def on_user_loop(self, agent_name: str, assistant_message: str):
        return input(f"{agent_name}: {assistant_message}: ")
    
    def on_tool_call(self, agent_name: str, fn_name: str, arguments: dict):
        print(f"{agent_name} ===> {fn_name}")

def main():
    coordinator = Agent(
        agent_name='coordinator',
        model_name='your_model_here',   # <- your_model_here
        instructions='You are a coordinator who manages image processing workflows. You can delegate tasks to image analyzers. When users ask about images, coordinate with your team to complete the request. you have to pass the image path to the image analyser to get insight.',
        tools=None,
        tool_choice=None,
        session=None,
        allow_user_input=True,
        max_turns=-1,
        callbacks=MyCallback(),
    )

    image_analyzer = Agent(
        agent_name='image_analyzer',
        model_name='your_model_here',   # <- your_model_here
        instructions='You are an image analyzer. given the img path, you have to read the image with given tool and read the image and analyse it and return the detailed information.',
        tools=Tools([read_image_tool]),
        tool_choice=None,
        session=None,
        allow_user_input=False,
        max_turns=-1,
        callbacks=None,
    )

    protocol = CommunicationProtocol(
        'coordinator<->image_analyzer',
        [coordinator, image_analyzer]
    )

    protocol.execute(input="Hello!")

if __name__ == '__main__':
    main()