import uuid
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from backend.app.providers.base import BaseProvider, CompletionRequest
from datetime import datetime

class MockProvider(BaseProvider):
    async def chat_completion(self, request: CompletionRequest, api_key: str) -> Dict[str, Any]:
        """Mocks a successful provider response."""
        response_id = f"mock-{uuid.uuid4()}"

        # Calculate mock token usage based roughly on input
        input_text = " ".join(str(m.get("content", "")) for m in request.messages)
        input_tokens = len(input_text.split()) + 5
        output_tokens = 15

        return {
            "id": response_id,
            "object": "chat.completion",
            "created": int(datetime.utcnow().timestamp()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a mocked response."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }

    async def stream_chat_completion(self, request: CompletionRequest, api_key: str) -> AsyncGenerator[str, None]:
        """Mocks a streaming provider response."""
        response_id = f"mock-{uuid.uuid4()}"
        created = int(datetime.utcnow().timestamp())

        words = ["This", " is", " a", " mocked", " streaming", " response."]

        for i, word in enumerate(words):
            chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": word} if i > 0 else {"role": "assistant", "content": word},
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.01)

        # Final chunk with finish reason and mock usage
        input_text = " ".join(str(m.get("content", "")) for m in request.messages)
        input_tokens = len(input_text.split()) + 5
        output_tokens = len(words)

        final_chunk = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
