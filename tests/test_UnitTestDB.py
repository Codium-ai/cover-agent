import pytest
import os
from datetime import datetime, timedelta
from cover_agent.UnitTestDB import UnitTestDB, UnitTestGenerationAttempt

DB_NAME = "unit_test_runs.db"
DATABASE_URL = f"sqlite:///{DB_NAME}"

@pytest.fixture(scope="class")
def unit_test_db():
    # Create an empty DB file for testing
    with open(DB_NAME, "w"):
        pass

    db = UnitTestDB(DATABASE_URL)
    yield db

    # Cleanup after tests
    db.engine.dispose()

    # Delete the db file
    os.remove(DB_NAME)

@pytest.mark.usefixtures("unit_test_db")
class TestUnitTestDB:

    def test_insert_attempt(self, unit_test_db):
        test_result = {
            "status": "success",
            "reason": "",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest"
            },
            "language": "python",
            "source_file": "sample source code",
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        attempt_id = unit_test_db.insert_attempt(test_result)
        with unit_test_db.Session() as session:
            attempt = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()

        assert attempt.id == attempt_id
        assert attempt.status == "success"
        assert attempt.reason == ""
        assert attempt.exit_code == 0
        assert attempt.stderr == ""
        assert attempt.stdout == "Test passed"
        assert attempt.test_code == "def test_example(): pass"
        assert attempt.imports == "import pytest"
        assert attempt.language == "python"
        assert attempt.source_file == "sample source code"
        assert attempt.original_test_file == "sample test code"
        assert attempt.processed_test_file == "sample new test code"

    def test_dump_to_report(self, unit_test_db, tmp_path):
        test_result = {
            "status": "success",
            "reason": "Test passed successfully",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest"
            },
            "language": "python",
            "source_file": "sample source code",
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        unit_test_db.insert_attempt(test_result)

        # Generate the report and save it to a temporary file
        report_filepath = tmp_path / "unit_test_report.html"
        unit_test_db.dump_to_report(str(report_filepath))

        # Check if the report was generated successfully
        assert os.path.exists(report_filepath)

        # Verify the report content
        with open(report_filepath, "r") as file:
            content = file.read()

        assert "sample test code" in content
        assert "sample new test code" in content
        assert "def test_example(): pass" in content
