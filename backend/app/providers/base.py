from typing import AsyncGenerator, Dict, Any, List
from pydantic import BaseModel

class CompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    stream: bool = False
    max_tokens: int = 1000
    temperature: float = 1.0

class BaseProvider:
    async def chat_completion(self, request: CompletionRequest, api_key: str) -> Dict[str, Any]:
        """
        Executes a standard non-streaming chat completion.
        Should return an OpenAI-compatible response dictionary.
        """
        raise NotImplementedError

    async def stream_chat_completion(self, request: CompletionRequest, api_key: str) -> AsyncGenerator[str, None]:
        """
        Executes a streaming chat completion.
        Should yield SSE formatted string chunks.
        """
        raise NotImplementedError
