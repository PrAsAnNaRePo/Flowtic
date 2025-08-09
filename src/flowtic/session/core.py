from typing import Any, Optional, List
from flowtic.session.base import SessionInterface
import os
import base64

class SessionManager(SessionInterface):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
    
    def _handle_image(self, image: str):
        if os.path.exists(image):
            with open(image, 'rb') as f:
                return f'data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}'
        else:
            return f'data:image/jpeg;base64,{image}'
            
    def add_user_context(self, tag: str, text: Optional[str] = None, images: Optional[List] = None):
        if text and images:
            self._buffer_memory[tag].append(
                {
                    'role': 'user',
                    'content':[
                        {'type': 'text', 'text': text},
                    ]
                }
            )
            for img in images:
                self._buffer_memory[tag][-1]['content'].append(
                    {'type': 'image_url', 'image_url': {'url': self._handle_image(img)}}
                )

        elif text:
            self._buffer_memory[tag].append(
                {
                    'role': 'user',
                    'content':[
                        {'type': 'text', 'text': text},
                    ]
                }
            )
        elif images:
            self._buffer_memory[tag].append(
                {
                    'role': 'user',
                    'content':[
                        {'type': 'image_url', 'image_url': {'url': self._handle_image(img)}} for img in images
                    ]
                }
            )
        else:
            raise ValueError("No input provided")
    
    def add_assistant_context(self, tag: str, ass_out: Any):
        self._buffer_memory[tag].append(
            ass_out
        )
    
    def add_tool_context(self, tag: str, fn_name, tool_call_id, output):
        self._buffer_memory[tag].append(
            {
                'tool_call_id': tool_call_id,
                'role': 'tool',
                'name': fn_name,
                'content': output
            }
        )
