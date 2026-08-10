import pytest
from backend.app.providers.mock import MockProvider
from backend.app.providers.base import CompletionRequest

@pytest.mark.asyncio
async def test_mock_provider_chat_completion():
    provider = MockProvider()
    request = CompletionRequest(
        model="mock-claude",
        messages=[{"role": "user", "content": "Hello"}],
        stream=False
    )

    response = await provider.chat_completion(request, "fake-key")

    assert response["object"] == "chat.completion"
    assert len(response["choices"]) == 1
    assert response["choices"][0]["message"]["content"] == "This is a mocked response."
    assert "usage" in response

@pytest.mark.asyncio
async def test_mock_provider_stream_completion():
    provider = MockProvider()
    request = CompletionRequest(
        model="mock-claude",
        messages=[{"role": "user", "content": "Hello"}],
        stream=True
    )

    chunks = []
    async for chunk in provider.stream_chat_completion(request, "fake-key"):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert chunks[-1] == "data: [DONE]\n\n"
