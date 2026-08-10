import json
import uuid
from typing import AsyncGenerator, Dict, Any, List
from fastapi import HTTPException
from anthropic import AsyncAnthropic, APIError, RateLimitError, AuthenticationError
from backend.app.providers.base import BaseProvider, CompletionRequest

class AnthropicProvider(BaseProvider):
    def _convert_messages_to_anthropic(self, messages: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        """Extracts system prompt and converts messages to Anthropic format."""
        system_prompt = ""
        anthropic_messages = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                system_prompt += content + "\n"
            elif role in ["user", "assistant"]:
                anthropic_messages.append({"role": role, "content": content})

        return system_prompt.strip(), anthropic_messages

    def _handle_anthropic_error(self, e: Exception):
        if isinstance(e, AuthenticationError):
            raise HTTPException(status_code=500, detail="Upstream authentication error")
        elif isinstance(e, RateLimitError):
            raise HTTPException(status_code=429, detail="Upstream rate limit exceeded")
        elif isinstance(e, APIError):
            raise HTTPException(status_code=502, detail="Upstream provider error")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

    async def chat_completion(self, request: CompletionRequest, api_key: str) -> Dict[str, Any]:
        client = AsyncAnthropic(api_key=api_key)
        system, messages = self._convert_messages_to_anthropic(request.messages)

        try:
            response = await client.messages.create(
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=system if system else None,
                messages=messages
            )

            # Convert to OpenAI format
            return {
                "id": response.id,
                "object": "chat.completion",
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response.content[0].text if response.content else ""
                        },
                        "finish_reason": response.stop_reason if response.stop_reason else "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
        except Exception as e:
            self._handle_anthropic_error(e)

    async def stream_chat_completion(self, request: CompletionRequest, api_key: str) -> AsyncGenerator[str, None]:
        client = AsyncAnthropic(api_key=api_key)
        system, messages = self._convert_messages_to_anthropic(request.messages)

        try:
            stream = await client.messages.create(
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=system if system else None,
                messages=messages,
                stream=True
            )

            response_id = f"chatcmpl-{uuid.uuid4()}"
            input_tokens = 0
            output_tokens = 0

            async for event in stream:
                if event.type == "message_start":
                    input_tokens = event.message.usage.input_tokens
                elif event.type == "content_block_delta":
                    chunk = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "model": request.model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": event.delta.text},
                                "finish_reason": None
                            }
                        ]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif event.type == "message_delta":
                    output_tokens = event.usage.output_tokens
                    if event.delta.stop_reason:
                        chunk = {
                            "id": response_id,
                            "object": "chat.completion.chunk",
                            "model": request.model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": event.delta.stop_reason
                                }
                            ],
                            "usage": {
                                "prompt_tokens": input_tokens,
                                "completion_tokens": output_tokens,
                                "total_tokens": input_tokens + output_tokens
                            }
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                elif event.type == "error":
                    yield f"data: {json.dumps({'error': 'Upstream stream error'})}\n\n"
                    break

            yield "data: [DONE]\n\n"

        except Exception as e:
            self._handle_anthropic_error(e)
