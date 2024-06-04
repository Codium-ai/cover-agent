import pytest
from unittest.mock import patch
from cover_agent.UnitTestGenerator import (
    UnitTestGenerator,
    extract_error_message_python, extract_error_message_jacoco, extract_error_message,
)
from cover_agent.ReportGenerator import ReportGenerator
import os


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
        )
        test_gen.relevant_line_number_to_insert_after = 10
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
        )
        test_gen.relevant_line_number_to_insert_after = 10
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

    def test_extracts_stdout_message_remove_irrelevant_output(self):
        fail_details = {
            "stdout": """> Task :clean
> Task :compileJava
> Task :compileGroovy NO-SOURCE
> Task :processResources NO-SOURCE
> Task :classes
> Task :compileTestJava NO-SOURCE
> Task :compileTestGroovy
> Task :processTestResources NO-SOURCE
> Task :testClasses

> Task :test

SimpleMathOperationsSpec > should return correct product when multiplying two positive integers FAILED
    org.spockframework.runtime.SpockComparisonFailure at SimpleMathOperationsSpec.groovy:37

> Task :test FAILED

Deprecated Gradle features were used in this build, making it incompatible with Gradle 9.0.

You can use '--warning-mode all' to show the individual deprecation warnings and determine if they come from your own scripts or plugins.

For more on this, please refer to https://docs.gradle.org/8.5/userguide/command_line_interface.html#sec:command_line_warnings in the Gradle documentation.
4 actionable tasks: 4 executed
""",
            "stderr": ""
        }
        result = extract_error_message_jacoco(fail_details)
        expected_message = ("SimpleMathOperationsSpec > should return correct product when multiplying two positive "
                            "integers FAILED")
        assert expected_message in result

    def test_extracts_stderr_message_general_failure(self):
        fail_details = {
            "stdout": "",
            "stderr": """startup failed: /Users/davidparry/code/github/cover-agent/templated_tests/java_gradle/src
            /test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy: 31: unable to resolve class Fibonacci 
            @ line 31, column 19. Fibonacci fibonacci = Mock(Fibonacci) ^

1 error


FAILURE: Build failed with an exception.

* What went wrong
Execution failed for task ':compileTestGroovy'.
> Compilation failed; see the compiler error output for details.

* Try:
> Run with --info option to get more log output.
> Run with --scan to get full insights.

BUILD FAILED in 1s"""
        }
        result = extract_error_message_jacoco(fail_details)
        expected_message = "SimpleMathOperationsSpec.groovy: 31: unable to resolve class Fibonacci"
        assert expected_message in result

    def test_extract_error_message_python_standard_failure(self):
        fail_details = {
            "stdout": "=== FAILURES ===\nE   AssertionError: assert 1 == 2\n===\n"
        }
        expected_output = "E   AssertionError: assert 1 == 2"
        result = extract_error_message(self, fail_details)
        assert result == expected_output

    def test_extract_error_message_jacoco_standard_failure(self):
        self.coverage_type = "jacoco"
        message = ("A Error message possibly for missing imports to can not compile bad syntax etc.. but not a failure "
                   "in a test.")
        fail_details = {
            "stdout": "",
            "stderr": message
        }
        result = extract_error_message(self, fail_details)
        assert result == message
