import asyncio
import json
from typing import Any, List, Optional

from flowtic.agents.base import AgentInterface


def _message_content_to_text(content: Any) -> Optional[str]:
    if content is None:
        return None

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        text_output = "\n".join(part for part in text_parts if part)
        return text_output or str(content)

    return str(content)

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
    
    def __call__(self, input: str, images: Optional[List] = None):
        """
        call the agent

        Args:
            input (str): The input to the agent.
            images (Optional[List], optional): List of images as a local file path or url or base64 encoded string. Defaults to None.
        """

        if self.verbose:
            print(f">> Staring {self.name} agent execution")

        self.add_context(input={'text': input, 'images': images})
        
        turn_count = 0
        final_output = None
        while True:
            if self.max_turns > 0 and turn_count >= self.max_turns:
                break
                
            response = self.completion()
            response_message = response.choices[0].message
            self.add_context(assistant_output=response_message)
            turn_count += 1
            message_text = _message_content_to_text(response_message.content)
            if message_text is not None:
                final_output = message_text

            tool_calls = response_message.tool_calls or []

            if tool_calls:
                communication_occurred = False
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    self._call_tool_callback(function_name, function_args)
                    if function_name == '_spin_into':
                        tool_output = self.tools.get_callable(function_name)(self.name, **function_args)
                        communication_occurred = True
                    else:
                        tool_output = self.tools.get_callable(function_name)(**function_args)

                    assert isinstance(tool_output, tuple), "Tool output should return a tuple of (text, images (none if no images))"
                    if tool_output[0] is not None:
                        final_output = str(tool_output[0])

                    self.add_context(tool_output={'fn_name': function_name, 'tool_call_id': tool_call.id, 'output': str(tool_output[0])})
                    if tool_output[1]:
                        self.add_context(input={'text': 'Here are the tool output images:\n', 'images': tool_output[1] \
                            if isinstance(tool_output[1], list) else [tool_output[1]]})
                
                # If agent communicated to another agent and doesn't allow user input, stop
                if communication_occurred and not self.allow_user_input:
                    break
                    
            else:
                if self.allow_user_input:
                    try:
                        user_input = self._call_user_loop(message_text or "")
                        self.add_context(input={'text': user_input})
                    except NotImplementedError:
                        break
                else:
                    break

        return final_output


class AsyncAgent(AgentInterface):
    def __init__(self, **kwargs):
        """
        Initialize the asyncronous agent.

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

    async def run_async_or_sync(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result 

    async def __call__(self, input: str, images: Optional[List] = None):
        """
        call the agent

        Args:
            input (str): The input to the agent.
            images (Optional[List], optional): List of images as a local file path or url or base64 encoded string. Defaults to None.
        """

        if self.verbose:
            print(f">> Staring {self.name} agent execution")

        self.add_context(input={'text': input, 'images': images})
        
        turn_count = 0
        final_output = None
        while True:
            if self.max_turns > 0 and turn_count >= self.max_turns:
                break
            if self.verbose: 
                print("Session Buffer:")
                print(self.session.get_buffer_memory(self.name))

            response = await self.acompletion()
            response_message = response.choices[0].message
            
            if self.verbose:
                print(response_message)

            self.add_context(assistant_output=response_message)
            turn_count += 1
            message_text = _message_content_to_text(response_message.content)
            if message_text is not None:
                final_output = message_text

            tool_calls = response_message.tool_calls or []

            if tool_calls:
                communication_occurred = False

                tasks = []
                tool_metadata = []
                for tool_call in tool_calls:
                    callable_func = self.tools.get_callable(tool_call.function.name)
                    args = json.loads(tool_call.function.arguments)
                    self._call_tool_callback(tool_call.function.name, args)

                    if tool_call.function.name == '_async_spin_into':
                        communication_occurred = True
                        task = asyncio.create_task(self.run_async_or_sync(callable_func, self.name, **args))
                    else:
                        task = asyncio.create_task(self.run_async_or_sync(callable_func, **args))

                    tasks.append(task)
                    tool_metadata.append({
                        'function_name': tool_call.function.name,
                        'tool_call': tool_call
                    })

                tool_outputs = await asyncio.gather(*tasks)

                for tool_output, metadata in zip(tool_outputs, tool_metadata):
                    if self.verbose:
                        print("TOOL OUTPUT: ")
                        print(tool_output)

                    # if metadata['function_name'] != '_async_spin_into':
                    assert isinstance(tool_output, tuple), "Tool output should return a tuple of (text, images (none if no images))"
                    self.add_context(tool_output={
                        'fn_name': metadata['function_name'],
                        'tool_call_id': metadata['tool_call'].id,
                        'output': str(tool_output[0])
                    })

                    if tool_output[1]:
                        self.add_context(input={'text': 'Here are the tool output images:\n', 'images': tool_output[1] \
                            if isinstance(tool_output[1], list) else [tool_output[1]]})
                
                # If agent communicated to another agent and doesn't allow user input, stop
                if communication_occurred and not self.allow_user_input:
                    break
                    
            else:
                if self.allow_user_input:
                    try:
                        user_input = self._call_user_loop(message_text or "")
                        self.add_context(input={'text': user_input})
                    except NotImplementedError:
                        break
                else:
                    break

        return final_output

