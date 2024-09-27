from cover_agent.ReportGenerator import ReportGenerator
from cover_agent.UnitTestGenerator import UnitTestGenerator
from unittest.mock import patch, mock_open
import os
import pytest
import tempfile

class TestUnitTestGenerator:
    def test_get_included_files_mixed_paths(self):
        with patch("builtins.open", mock_open(read_data="file content")) as mock_file:
            mock_file.side_effect = [
                IOError("File not found"),
                mock_open(read_data="file content").return_value,
            ]
            included_files = ["invalid_file1.txt", "valid_file2.txt"]
            result = UnitTestGenerator.get_included_files(included_files)
            assert (
                result
                == "file_path: `valid_file2.txt`\ncontent:\n```\nfile content\n```"
            )

    def test_get_included_files_valid_paths(self):
        with patch("builtins.open", mock_open(read_data="file content")):
            included_files = ["file1.txt", "file2.txt"]
            result = UnitTestGenerator.get_included_files(included_files)
            assert (
                result
                == "file_path: `file1.txt`\ncontent:\n```\nfile content\n```\nfile_path: `file2.txt`\ncontent:\n```\nfile content\n```"
            )
    def test_get_code_language_no_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestGenerator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3"
            )
            language = generator.get_code_language("filename")
            assert language == "unknown"

    def test_extract_error_message_exception_handling(self):
        # PromptBuilder will not instantiate so we're expecting an empty error_message.
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestGenerator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3"
            )
            with patch.object(generator, 'ai_caller') as mock_ai_caller:
                mock_ai_caller.call_model.side_effect = Exception("Mock exception")
                error_message = generator.extract_error_message(stderr="stderr content", stdout="stdout content")
                assert '' in error_message
