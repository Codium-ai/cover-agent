import pytest
from datetime import datetime, timedelta
from cover_agent.UnitTestDB import UnitTestDB, UnitTestGenerationAttempt

DATABASE_URL = 'sqlite:///unit_test_runs.db'

@pytest.fixture(scope='module')
def unit_test_db():
    db = UnitTestDB(DATABASE_URL)
    yield db
    # Cleanup after tests
    db.engine.dispose()

def test_insert_attempt(unit_test_db):
    run_time = datetime.utcnow()
    llm_info = {"model": "GPT-4"}
    prompt = {"input": "Generate tests"}
    generated_test = "def test_example(): pass"
    imports = "import pytest"
    stdout = "Test passed"
    stderr = ""

    attempt_id = unit_test_db.insert_attempt(run_time, llm_info, prompt, generated_test, imports, stdout, stderr)
    with unit_test_db.Session() as session:
        attempt = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()

    assert attempt.id == attempt_id
    assert attempt.run_time == run_time
    assert attempt.llm_info == llm_info
    assert attempt.prompt == prompt
    assert attempt.generated_test == generated_test
    assert attempt.imports == imports
    assert attempt.stdout == stdout
    assert attempt.stderr == stderr

def test_select_all_attempts(unit_test_db):
    attempts = unit_test_db.select_all_attempts()
    assert len(attempts) > 0

def test_select_attempt(unit_test_db):
    run_time = datetime.utcnow()
    llm_info = {"model": "GPT-4"}
    prompt = {"input": "Generate tests"}
    generated_test = "def test_example(): pass"
    imports = "import pytest"
    stdout = "Test passed"
    stderr = ""

    attempt_id = unit_test_db.insert_attempt(run_time, llm_info, prompt, generated_test, imports, stdout, stderr)
    attempt = unit_test_db.select_attempt(attempt_id)

    assert attempt is not None
    assert attempt.id == attempt_id

def test_select_attempt_in_range(unit_test_db):
    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow() + timedelta(days=1)

    run_time = datetime.utcnow()
    llm_info = {"model": "GPT-4"}
    prompt = {"input": "Generate tests"}
    generated_test = "def test_example(): pass"
    imports = "import pytest"
    stdout = "Test passed"
    stderr = ""

    unit_test_db.insert_attempt(run_time, llm_info, prompt, generated_test, imports, stdout, stderr)
    attempts = unit_test_db.select_attempt_in_range(start_time, end_time)

    assert len(attempts) > 0

def test_select_attempt_flat(unit_test_db):
    run_time = datetime.utcnow()
    llm_info = {"model": "GPT-4", "version": "3.5"}
    prompt = {"input": "Generate tests"}
    generated_test = "def test_example(): pass"
    imports = "import pytest"
    stdout = "Test passed"
    stderr = ""

    attempt_id = unit_test_db.insert_attempt(run_time, llm_info, prompt, generated_test, imports, stdout, stderr)
    flat_attempt = unit_test_db.select_attempt_flat(attempt_id)

    assert flat_attempt is not None
    assert flat_attempt['id'] == attempt_id
    assert flat_attempt['model'] == "GPT-4"
    assert flat_attempt['version'] == "3.5"
