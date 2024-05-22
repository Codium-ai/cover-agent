import pytest
from unittest.mock import patch
from cover_agent.AICaller import AICaller

class TestAICaller:
    @pytest.fixture
    def ai_caller(self):
        return AICaller("test-model", "test-api")

    @patch('cover_agent.AICaller.AICaller.call_model')
    def test_call_model_simplified(self, mock_call_model):
        # Setup the mock to return a predefined response
        mock_call_model.return_value = ("Hello world!", 2, 10)

        ai_caller = AICaller("test-model", "test-api")
        # Explicitly provide the default value of max_tokens
        response, prompt_tokens, response_tokens = ai_caller.call_model("Hello, world!", max_tokens=4096)

        # Assertions to check if the returned values are as expected
        assert response == "Hello world!"
        assert prompt_tokens == 2
        assert response_tokens == 10

        # Check if call_model was called correctly
        mock_call_model.assert_called_once_with("Hello, world!", max_tokens=4096)

    @patch('cover_agent.AICaller.litellm.completion')
    def test_call_model_with_error(self, mock_completion, ai_caller):
        # Set up mock to raise an exception
        mock_completion.side_effect = Exception("Test exception")

        # Call the method and handle the exception
        with pytest.raises(Exception) as exc_info:
            ai_caller.call_model("Hello, world!")
        
        assert str(exc_info.value) == "Test exception"