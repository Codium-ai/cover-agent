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
    def test_initialization_with_api_key_env(self, mock_openai, api_key):
        # Test successful initialization with OPENAI_API_KEY set
        AICaller(model="test-model")
        mock_openai.assert_called_with(api_key="fake_api_key")
    
    def test_initialization_with_api_key_and_base_url_env(self, mock_openai, monkeypatch, api_key):
        # Mock the base URL for this specific test
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://fake-base-url.com/v1")
        
        # Test successful initialization with OPENAI_API_KEY set and OPENAI_API_BASE_URL set
        AICaller(model="test-model")
        mock_openai.assert_called_with(base_url="https://fake-base-url.com/v1", api_key="fake_api_key")


    def test_count_tokens(self, mock_openai, aicaller):
        # Test that count_tokens correctly counts the tokens of the input text
        token_count = aicaller.count_tokens("Test string")
        assert (
            token_count == 100
        ), "The count_tokens method did not return the expected token count."

    def test_initialization_without_api_key_env(self, mock_openai, monkeypatch):
        # Test initialization failure when OPENAI_API_KEY is not set
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError) as exc_info:
            AICaller(model="test-model")
        assert "OPENAI_API_KEY environment variable not found." in str(exc_info.value)

    def test_initialization_with_failed_encoding(
        self, mock_openai, monkeypatch, encoding_mock, api_key
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
    
    @pytest.mark.parametrize(
        "model, expected_encoding",
        [
            ("gpt-4o", "o200k_base"),
            ("gpt-4", "cl100k_base"),
            ("gpt-4-turbo", "cl100k_base"),
        ],
    )
    def test_should_get_right_encoding_based_on_model(self, mock_openai, api_key, model, expected_encoding, encoding_mock):
        # Test that the correct encoding is retrieved based on the model
        ai_caller = AICaller(model=model)
        ai_caller._get_encoder()
        encoding_mock.assert_called_with(expected_encoding)

    

