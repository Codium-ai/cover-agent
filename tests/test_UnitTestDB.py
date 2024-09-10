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
                "new_imports_code": "import pytest",
            },
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        attempt_id = unit_test_db.insert_attempt(test_result)
        with unit_test_db.Session() as session:
            attempt = (
                session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()
            )

        assert attempt.id == attempt_id
        assert attempt.status == "success"
        assert attempt.reason == ""
        assert attempt.exit_code == 0
        assert attempt.stderr == ""
        assert attempt.stdout == "Test passed"
        assert attempt.test_code == "def test_example(): pass"
        assert attempt.imports == "import pytest"
        assert attempt.original_test_file == "sample test code"
        assert attempt.processed_test_file == "sample new test code"

    def test_select_all_attempts(self, unit_test_db):
        test_result = {
            "status": "success",
            "reason": "",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest",
            },
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        unit_test_db.insert_attempt(test_result)
        attempts = unit_test_db.select_all_attempts()
        assert len(attempts) > 0

        # Validate the new fields in the first attempt
        first_attempt = attempts[0]
        assert first_attempt.original_test_file == "sample test code"
        assert first_attempt.processed_test_file == "sample new test code"

    def test_select_attempt(self, unit_test_db):
        test_result = {
            "status": "success",
            "reason": "",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest",
            },
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        attempt_id = unit_test_db.insert_attempt(test_result)
        attempt = unit_test_db.select_attempt(attempt_id)

        assert attempt is not None
        assert attempt.id == attempt_id
        assert attempt.original_test_file == "sample test code"
        assert attempt.processed_test_file == "sample new test code"

    def test_select_attempt_in_range(self, unit_test_db):
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now() + timedelta(days=1)

        test_result = {
            "status": "success",
            "reason": "",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest",
            },
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        unit_test_db.insert_attempt(test_result)
        attempts = unit_test_db.select_attempt_in_range(start_time, end_time)

        assert len(attempts) > 0

        # Validate the new fields in the first attempt
        first_attempt = attempts[0]
        assert first_attempt.original_test_file == "sample test code"
        assert first_attempt.processed_test_file == "sample new test code"

    def test_select_attempt_flat(self, unit_test_db):
        test_result = {
            "status": "success",
            "reason": "",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest",
            },
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        attempt_id = unit_test_db.insert_attempt(test_result)
        flat_attempt = unit_test_db.select_attempt_flat(attempt_id)

        print(f"FLAT ATTEMPT: {flat_attempt}")

        assert flat_attempt is not None
        assert flat_attempt["id"] == attempt_id
        assert flat_attempt["status"] == "success"
        assert flat_attempt["stdout"] == "Test passed"
        assert flat_attempt["original_test_file"] == "sample test code"
        assert flat_attempt["processed_test_file"] == "sample new test code"
