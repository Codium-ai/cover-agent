import pytest
from cover_agent.UnitTestGenerator import (
    UnitTestGenerator,
    extract_error_message_python,
)
from cover_agent.ReportGenerator import ReportGenerator
import os

from unittest.mock import patch, mock_open


class TestUnitTestGenerator:
    def test_end_to_end1(self):
        # Test model definitions
        GPT4_TURBO = "gpt-4-turbo-2024-04-09"
        GPT35_TURBO = "gpt-3.5-turbo-0125"
        MAX_TOKENS = 4096

        DRY_RUN = True  # Unit tests should not be making calls to the LLM model
        CANNED_TESTS = {
            "new_tests": [
                {
                    "test_code": 'def test_current_date():\n    response = client.get("/current-date")\n    assert response.status_code == 200\n    assert "date" in response.json()'
                },
                {
                    "test_code": 'def test_add():\n    response = client.get("/add/2/3")\n    assert response.status_code == 200\n    assert "result" in response.json()\n    assert response.json()["result"] == 5'
                },
            ]
        }

        REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        TEST_FILE = f"{REPO_ROOT}/templated_tests/python_fastapi/test_app.py"

        # Read in file contents of sample test file so we can roll it back later
        with open(TEST_FILE, "r") as f:
            original_file_contents = f.read()

        # Instantiate a UnitTestGenerator with the test parameters
        test_gen = UnitTestGenerator(
            source_file_path=f"{REPO_ROOT}/templated_tests/python_fastapi/app.py",
            test_file_path=TEST_FILE,
            code_coverage_report_path=f"{REPO_ROOT}/templated_tests/python_fastapi/coverage.xml",
            llm_model=GPT35_TURBO,
            test_command="pytest --cov=. --cov-report=xml",
            test_command_dir=f"{REPO_ROOT}/templated_tests/python_fastapi",
            included_files=None,
            test_db_connection_string="sqlite:///unit_test_runs.sqlite",
        )
        test_gen.relevant_line_number_to_insert_tests_after = 10
        test_gen.test_headers_indentation = 4

        # Generate the tests
        generated_tests = (
            CANNED_TESTS
            if DRY_RUN
            else test_gen.generate_tests(max_tokens=MAX_TOKENS, dry_run=DRY_RUN)
        )

        # Validate the generated tests and generate a report
        results_list = [
            test_gen.validate_test(generated_test, generated_tests)
            for generated_test in generated_tests["new_tests"]
        ]
        ReportGenerator.generate_report(results_list, "test_results.html")

        # Write back sample test file contents
        with open(TEST_FILE, "w") as f:
            f.write(original_file_contents)

    def test_end_to_end2(self):
        # Test model definitions
        GPT4_TURBO = "gpt-4-turbo-2024-04-09"
        GPT35_TURBO = "gpt-3.5-turbo-0125"
        MAX_TOKENS = 4096

        DRY_RUN = True  # Unit tests should not be making calls to the LLM model
        CANNED_TESTS = {
            "language": "python",
            "new_tests": [
                {
                    "test_code": 'def test_current_date():\n    response = client.get("/current-date")\n    assert response.status_code == 200\n    assert "date" in response.json()',
                    "new_imports_code": "",
                },
                {
                    "test_code": 'def test_add():\n    response = client.get("/add/2/3")\n    assert response.status_code == 200\n    assert "result" in response.json()\n    assert response.json()["result"] == 5'
                },
            ],
        }

        REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        TEST_FILE = f"{REPO_ROOT}/templated_tests/python_fastapi/test_app.py"

        # Read in file contents of sample test file so we can roll it back later
        with open(TEST_FILE, "r") as f:
            original_file_contents = f.read()

        # Instantiate a UnitTestGenerator with the test parameters
        test_gen = UnitTestGenerator(
            source_file_path=f"{REPO_ROOT}/templated_tests/python_fastapi/app.py",
            test_file_path=TEST_FILE,
            code_coverage_report_path=f"{REPO_ROOT}/templated_tests/python_fastapi/coverage.xml",
            llm_model=GPT35_TURBO,
            test_command="pytest --cov=. --cov-report=xml",
            test_command_dir=f"{REPO_ROOT}/templated_tests/python_fastapi",
            included_files=None,
            test_db_connection_string="sqlite:///unit_test_runs.sqlite",
        )
        test_gen.relevant_line_number_to_insert_tests_after = 10
        test_gen.test_headers_indentation = 4

        # Generate the tests
        generated_tests = (
            CANNED_TESTS
            if DRY_RUN
            else test_gen.generate_tests(max_tokens=MAX_TOKENS, dry_run=DRY_RUN)
        )

        # Validate the generated tests and generate a report
        results_list = [
            test_gen.validate_test(generated_test, generated_tests)
            for generated_test in generated_tests["new_tests"]
        ]
        ReportGenerator.generate_report(results_list, "test_results.html")

        # Write back sample test file contents
        with open(TEST_FILE, "w") as f:
            f.write(original_file_contents)

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


class TestExtractErrorMessage:
    def test_extract_single_match(self):
        fail_message = "=== FAILURES ===\\nError occurred here\\n=== END ==="
        expected = "\\nError occurred here\\n"
        result = extract_error_message_python(fail_message)
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_extract_bad_match(self):
        fail_message = 33
        expected = ""
        result = extract_error_message_python(fail_message)
        assert result == expected, f"Expected '{expected}', got '{result}'"
