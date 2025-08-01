from typing import List, Optional
from flowtic.agents.base import AgentInterface
import json

class Agent(AgentInterface):
    def __init__(self, **kwargs):
        """
        Initialize the agent.

        Args:
            model_name (str): The litellm compatible model name.
            instructions (str | None, optional): The instructions for the agent. Defaults to "You are a helpful assistant."
            tools (Optional[List], optional): The tools to execute for the agent. Defaults to None.
            tool_choice (str, optional): The tool choice for the agent. Defaults to "none".
            session (Optional[SessionManager], optional): The session for the agent to keep context. Defaults to None.
            allow_user_input (bool, optional): Whether to allow the model to take user input. Defaults to True.
            max_turns (int, optional): The maximum number of turns. Defaults to -1 (unlimited).
        """
        super().__init__(**kwargs)

        if not self.model_name.startswith(('openai', 'anthropic', 'azure')):
            raise ValueError(f"Currently only OpenAI, Anthropic and Azure models are supported. Model Passed: {self.model_name}")
    
    def __call__(self, input: str, images: Optional[List] = None):
        """
        call the agent

        Args:
            input (str): The input to the agent.
            images (Optional[List], optional): List of images as a local file path or url or base64 encoded string. Defaults to None.
        """

        self.add_context(input={'text': input, 'images': images})

        while True:
            response = self.completion()
            response_message = response.choices[0].message
            self.add_context(assistant_output=response_message)

            tool_calls = response_message.tool_calls

            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    self.callbacks.on_tool_call(self.name, function_name, function_args)
                    tool_output = self.tools.get_callable(function_name)(**function_args)

                    assert isinstance(tool_output, tuple), "Tool output should return a tuple of (text, images (none if no images))"

                    self.add_context(tool_output={'fn_name': function_name, 'tool_call_id': tool_call.id, 'output': tool_output[0]})
                    if tool_output[1]:
                        self.add_context(input={'text': 'Here are the tool output images:\n', 'images': tool_output[1] \
                            if isinstance(tool_output[1], list) else [tool_output[1]]})
            else:
                try:
                    user_input = self.callbacks.on_user_loop(self.name, response_message.content)
                except NotImplementedError:
                    user_input = "YOU ARE NOT ALLOWED TO DIRECTLY SPEAK WITH USER, CONTACT THE APPROPRIATE AGENT"
                self.add_context(input={'text': user_input})



                






        
            





