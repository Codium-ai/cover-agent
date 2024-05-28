import pytest
from unittest.mock import patch
from cover_agent.UnitTestGenerator import UnitTestGenerator
from cover_agent.ReportGenerator import ReportGenerator
import os


class TestUnitTestGenerator:
    def test_end_to_end1(self):
        # Test model definitions
        GPT4_TURBO = "gpt-4-turbo-2024-04-09"
        GPT35_TURBO = "gpt-3.5-turbo-0125"
        MAX_TOKENS = 4096

        DRY_RUN = True  # Unit tests should not be making calls to the LLM model
        CANNED_TESTS = {'tests':[
            {'test_code': 'def test_current_date():\n    response = client.get("/current-date")\n    assert response.status_code == 200\n    assert "date" in response.json()'},
            {'test_code':'def test_add():\n    response = client.get("/add/2/3")\n    assert response.status_code == 200\n    assert "result" in response.json()\n    assert response.json()["result"] == 5'},
        ]}

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
            test_gen.validate_test(generated_test, generated_tests) for generated_test in generated_tests['tests']
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
        CANNED_TESTS = {'language': 'python',
                        'relevant_line_number_to_insert_after': 10,
                        'needed_indent': 4,
            'tests':[
            {'test_code': 'def test_current_date():\n    response = client.get("/current-date")\n    assert response.status_code == 200\n    assert "date" in response.json()', "new_imports_code":""},
            {'test_code':'def test_add():\n    response = client.get("/add/2/3")\n    assert response.status_code == 200\n    assert "result" in response.json()\n    assert response.json()["result"] == 5'},
        ]}

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
            test_gen.validate_test(generated_test, generated_tests) for generated_test in generated_tests['tests']
        ]
        ReportGenerator.generate_report(results_list, "test_results.html")

        # Write back sample test file contents
        with open(TEST_FILE, "w") as f:
            f.write(original_file_contents)
