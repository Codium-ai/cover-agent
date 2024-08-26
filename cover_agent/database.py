from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound


Base = declarative_base()

class UnitTestGenerationAttempt(Base):
    __tablename__ = 'unit_test_generation_attempts'
    id = Column(Integer, primary_key=True)
    run_time = Column(DateTime, default=datetime.utcnow)
    llm_info = Column(JSON)
    prompt = Column(JSON)
    generated_test = Column(Text)
    imports = Column(Text)
    stdout = Column(Text)
    stderr = Column(Text)

# Connect to the database
engine = create_engine('sqlite:///test_runs.db')  # Replace with your DB connection string
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def insert_attempt(run_time, llm_info, prompt, generated_test, imports, stdout, stderr):
    new_attempt = UnitTestGenerationAttempt(
        run_time=run_time,
        llm_info=llm_info,
        prompt=prompt,
        generated_test=generated_test,
        imports=imports,
        stdout=stdout,
        stderr=stderr
    )
    session.add(new_attempt)
    session.commit()
    return new_attempt.id

def select_all_attempts():
    return session.query(UnitTestGenerationAttempt).all()

def select_attempt(attempt_id):
    try:
        return session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()
    except NoResultFound:
        return None

def select_attempt_in_range(start: datetime, end: datetime):
    return session.query(UnitTestGenerationAttempt).filter(UnitTestGenerationAttempt.run_time >= start, UnitTestGenerationAttempt.run_time <= end).all()

def select_attempt_flat(attempt_id):
    try:
        result = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one().__dict__
        llm_info = result.pop('llm_info', {})
        if isinstance(llm_info, dict):
            result.update(llm_info)
        return result
    except NoResultFound:
        return None