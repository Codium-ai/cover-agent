import pytest
from unittest.mock import patch
from cover_agent.AICaller import AICaller


@pytest.fixture
def api_key(monkeypatch):
    # Setup: Provide a fake API key
    monkeypatch.setenv("OPENAI_API_KEY", "fake_api_key")


@pytest.fixture
def encoding_mock():
    # Mock for tiktoken encoding functionality
    with patch("cover_agent.AICaller.tiktoken.get_encoding") as mock_encoding:
        mock_encoding.return_value.encode.return_value = [
            0
        ] * 100  # Simulates encoding to 100 tokens
        yield mock_encoding


@pytest.fixture
def aicaller(api_key, encoding_mock):
    # Provides an AICaller instance with a test model for each test, includes encoding mock
    return AICaller(model="test-model")


@patch("cover_agent.AICaller.OpenAI")  # Adjust the patch path as necessary
class TestAICaller:
    def test_initialization_with_env_var(self, mock_openai, api_key):
        # Test successful initialization with OPENAI_API_KEY set
        AICaller(model="test-model")
        mock_openai.assert_called_with(api_key="fake_api_key")

    def test_count_tokens(self, mock_openai, aicaller):
        # Test that count_tokens correctly counts the tokens of the input text
        token_count = aicaller.count_tokens("Test string")
        assert (
            token_count == 100
        ), "The count_tokens method did not return the expected token count."

    def test_initialization_without_env_var(self, mock_openai, monkeypatch):
        # Test initialization failure when OPENAI_API_KEY is not set
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError) as exc_info:
            AICaller(model="test-model")
        assert "OPENAI_API_KEY environment variable not found." in str(exc_info.value)

    def test_initialization_with_failed_encoding(
        self, mock_openai, monkeypatch, encoding_mock
    ):
        # Test initialization failure when encoding retrieval fails
        encoding_mock.side_effect = Exception("Encoding retrieval failed")
        with pytest.raises(ValueError) as exc_info:
            AICaller(model="test-model")
        assert "Failed to get encoding: Encoding retrieval failed" in str(
            exc_info.value
        )

    def test_count_tokens_encoding_error(self, mock_openai, aicaller, encoding_mock):
        # Test count_tokens method to handle encoding errors
        encoding_mock.return_value.encode.side_effect = Exception("Encoding error")
        with pytest.raises(ValueError) as exc_info:
            aicaller.count_tokens("Test string")
        assert "Error encoding text: Encoding error" in str(exc_info.value)
