import pytest
from unittest.mock import patch
from cover_agent.UnitTestGenerator import UnitTestGenerator
from cover_agent.ReportGenerator import ReportGenerator
import os


class TestUnitTestGenerator:
    def test_end_to_end(self):
        # Test model definitions
        GPT4_TURBO = "gpt-4-turbo-2024-04-09"
        GPT35_TURBO = "gpt-3.5-turbo-0125"
        MAX_TOKENS = 4096

        DRY_RUN = True  # Unit tests should not be making calls to the LLM model
        CANNED_TESTS = [
            'def test_current_date():\n    response = client.get("/current-date")\n    assert response.status_code == 200\n    assert "date" in response.json()',
            'def test_add():\n    response = client.get("/add/2/3")\n    assert response.status_code == 200\n    assert "result" in response.json()\n    assert response.json()["result"] == 5',
            'def test_subtract():\n    response = client.get("/subtract/5/2")\n    assert response.status_code == 200\n    assert "result" in response.json()\n    assert response.json()["result"] == 3',
            'def test_multiply():\n    response = client.get("/multiply/2/4")\n    assert response.status_code == 200\n    assert "result" in response.json()\n    assert response.json()["result"] == 8',
            'def test_divide():\n    response = client.get("/divide/10/2")\n    assert response.status_code == 200\n    assert "result" in response.json()\n    assert response.json()["result"] == 5',
            'def test_square():\n    response = client.get("/square/4")\n    assert response.status_code == 200\n    assert "result" in response.json()\n    assert response.json()["result"] == 16',
            'def test_is_palindrome():\n    response = client.get("/is-palindrome/radar")\n    assert response.status_code == 200\n    assert response.json()["is_palindrome"] == True',
            'def test_days_until_new_year():\n    response = client.get("/days-until-new-year")\n    assert response.status_code == 200\n    assert "days_until_new_year" in response.json()',
        ]

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

        # Generate the tests
        generated_tests = (
            CANNED_TESTS
            if DRY_RUN
            else test_gen.generate_tests(max_tokens=MAX_TOKENS, dry_run=DRY_RUN)
        )

        # Validate the generated tests and generate a report
        results_list = [
            test_gen.validate_test(generated_test) for generated_test in generated_tests
        ]
        ReportGenerator.generate_report(results_list, "test_results.html")

        # Write back sample test file contents
        with open(TEST_FILE, "w") as f:
            f.write(original_file_contents)
