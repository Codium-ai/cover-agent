import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cover_agent.database.db import Base, UnitTestGenerationAttempt, insert_attempt, select_all_attempts, select_attempt, select_attempt_in_range, select_attempt_flat

DATABASE_URL = 'sqlite:///cover_agent.db'

@pytest.fixture(scope='module')
def test_session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_insert_attempt(test_session):
    run_time = datetime.utcnow()
    llm_info = {"model": "GPT-3"}
    prompt = {"input": "Generate tests"}
    generated_test = "def test_example(): pass"
    imports = "import pytest"
    stdout = "Test passed"
    stderr = ""
    
    attempt_id = insert_attempt(run_time, llm_info, prompt, generated_test, imports, stdout, stderr)
    attempt = test_session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()
    
    assert attempt.id == attempt_id
    assert attempt.run_time == run_time
    assert attempt.llm_info == llm_info
    assert attempt.prompt == prompt
    assert attempt.generated_test == generated_test
    assert attempt.imports == imports
    assert attempt.stdout == stdout
    assert attempt.stderr == stderr

def test_select_all_attempts(test_session):
    attempts = select_all_attempts()
    assert len(attempts) > 0

def test_select_attempt(test_session):
    run_time = datetime.utcnow()
    llm_info = {"model": "GPT-3"}
    prompt = {"input": "Generate tests"}
    generated_test = "def test_example(): pass"
    imports = "import pytest"
    stdout = "Test passed"
    stderr = ""
    
    attempt_id = insert_attempt(run_time, llm_info, prompt, generated_test, imports, stdout, stderr)
    attempt = select_attempt(attempt_id)
    
    assert attempt is not None
    assert attempt.id == attempt_id

def test_select_attempt_in_range(test_session):
    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow() + timedelta(days=1)
    
    run_time = datetime.utcnow()
    llm_info = {"model": "GPT-3"}
    prompt = {"input": "Generate tests"}
    generated_test = "def test_example(): pass"
    imports = "import pytest"
    stdout = "Test passed"
    stderr = ""
    
    insert_attempt(run_time, llm_info, prompt, generated_test, imports, stdout, stderr)
    attempts = select_attempt_in_range(start_time, end_time)
    
    assert len(attempts) > 0

def test_select_attempt_flat(test_session):
    run_time = datetime.utcnow()
    llm_info = {"model": "GPT-3", "version": "3.5"}
    prompt = {"input": "Generate tests"}
    generated_test = "def test_example(): pass"
    imports = "import pytest"
    stdout = "Test passed"
    stderr = ""
    
    attempt_id = insert_attempt(run_time, llm_info, prompt, generated_test, imports, stdout, stderr)
    flat_attempt = select_attempt_flat(attempt_id)
    
    assert flat_attempt is not None
    assert flat_attempt['id'] == attempt_id
    assert flat_attempt['model'] == "GPT-3"
    assert flat_attempt['version'] == "3.5"