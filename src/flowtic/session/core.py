import base64
import binascii
import io
import mimetypes
import os
from typing import Any, List, Optional

from PIL import Image

from flowtic.session.base import SessionInterface

class SessionManager(SessionInterface):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
    
    def _encode_image_bytes(self, image_bytes: bytes, mime_type: str) -> str:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    def _handle_image(self, image: Any):
        if isinstance(image, Image.Image):
            buffered = io.BytesIO()
            image_format = (image.format or "PNG").upper()
            image.save(buffered, format=image_format)
            return self._encode_image_bytes(buffered.getvalue(), f"image/{image_format.lower()}")

        if isinstance(image, bytes):
            return self._encode_image_bytes(image, "image/jpeg")

        if not isinstance(image, str):
            raise TypeError("Images must be file paths, URLs, base64 strings, bytes, or PIL images")

        normalized_image = image.strip()

        if normalized_image.startswith(("http://", "https://", "data:image/")):
            return normalized_image

        if os.path.exists(normalized_image):
            mime_type = mimetypes.guess_type(normalized_image)[0] or "image/jpeg"
            with open(normalized_image, "rb") as file_handle:
                return self._encode_image_bytes(file_handle.read(), mime_type)

        try:
            base64.b64decode(normalized_image, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(
                "Images must be valid local paths, URLs, data URLs, or raw base64 strings"
            ) from exc

        return f"data:image/jpeg;base64,{normalized_image}"
            
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
