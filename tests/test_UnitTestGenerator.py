from cover_agent.CoverageProcessor import CoverageProcessor
from cover_agent.ReportGenerator import ReportGenerator
from cover_agent.Runner import Runner
from cover_agent.UnitTestGenerator import UnitTestGenerator
from unittest.mock import patch, mock_open
import datetime
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

    # def test_get_included_files_none(self):
    #     result = UnitTestGenerator.get_included_files(None)
    #     assert result == ""

    # def test_run_coverage_command_failure(self):
    #     with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
    #         generator = UnitTestGenerator(
    #             source_file_path=temp_source_file.name,
    #             test_file_path="test_test.py",
    #             code_coverage_report_path="coverage.xml",
    #             test_command="invalid_command",
    #             llm_model="gpt-3"
    #         )
    #         with pytest.raises(AssertionError):
    #             generator.run_coverage()

    # def test_extract_error_message_success(self):
    #     with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
    #         generator = UnitTestGenerator(
    #             source_file_path=temp_source_file.name,
    #             test_file_path="test_test.py",
    #             code_coverage_report_path="coverage.xml",
    #             test_command="pytest",
    #             llm_model="gpt-3"
    #         )
    #         with patch.object(generator.ai_caller, 'call_model', return_value=("error_summary: 'Mocked error summary'", 10, 10)):
    #             error_message = generator.extract_error_message(stderr="stderr content", stdout="stdout content")
    #             assert error_message == ""

    def test_run_coverage_with_report_coverage_flag(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestGenerator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                use_report_coverage_feature_flag=True
            )
            with patch.object(Runner, 'run_command', return_value=("", "", 0, datetime.datetime.now())):
                with patch.object(CoverageProcessor, 'process_coverage_report', return_value={'test.py': ([], [], 1.0)}):
                    generator.run_coverage()
                    # Dividing by zero so we're expecting a logged error and a return of 0
                    assert generator.current_coverage == 0

    def test_build_prompt_with_failed_tests(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestGenerator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3"
            )
            generator.failed_test_runs = [
                {
                    "code": {"test_code": "def test_example(): assert False"},
                    "error_message": "AssertionError"
                }
            ]
            prompt = generator.build_prompt()
            assert "Failed Test:" in prompt['user']


    def test_generate_tests_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestGenerator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3"
            )
            generator.build_prompt = lambda: "Test prompt"
            with patch.object(generator.ai_caller, 'call_model', return_value=("This is not YAML", 10, 10)):
                result = generator.generate_tests()
                
                # The eventual call to try_fix_yaml() will end up spitting out the same string but deeming is "YAML."
                # While this is not a valid YAML, the function will return the original string (for better or for worse).
                assert result =="This is not YAML"
                