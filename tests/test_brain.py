import pytest

from aria.brain import BrainRequest, MockBrain, OpenAIResponsesBrain, create_brain
from aria.config import Settings


@pytest.mark.asyncio
async def test_mock_brain_generates_deterministic_response():
    brain = MockBrain(model="test-model")

    response = await brain.generate(BrainRequest(prompt="hello", system="system"))

    assert response.provider == "mock"
    assert response.model == "test-model"
    assert "hello" in response.text


def test_create_brain_uses_mock_without_openai_key(tmp_path):
    settings = Settings(workspace=tmp_path, openai_api_key=None, model="test-model")

    brain = create_brain(settings)

    assert isinstance(brain, MockBrain)


def test_create_brain_uses_openai_with_openai_key(tmp_path):
    settings = Settings(workspace=tmp_path, openai_api_key="test-key", model="test-model")

    brain = create_brain(settings)

    assert isinstance(brain, OpenAIResponsesBrain)
    assert brain.provider == "openai"
    assert brain.model == "test-model"
