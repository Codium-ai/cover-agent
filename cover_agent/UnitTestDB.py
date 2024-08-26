from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, load_only
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

class UnitTestDB:
    def __init__(self, db_connection_string):
        self.engine = create_engine(db_connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def insert_attempt(self, run_time, llm_info, prompt, generated_test, imports, stdout, stderr):
        with self.Session() as session:
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

    def select_all_attempts(self):
        with self.Session() as session:
            return session.query(UnitTestGenerationAttempt).all()

    def select_attempt(self, attempt_id):
        with self.Session() as session:
            try:
                return session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()
            except NoResultFound:
                return None

    def select_attempt_in_range(self, start: datetime, end: datetime):
        with self.Session() as session:
            return session.query(UnitTestGenerationAttempt).filter(
                UnitTestGenerationAttempt.run_time >= start,
                UnitTestGenerationAttempt.run_time <= end
            ).all()

    def select_attempt_flat(self, attempt_id):
        with self.Session() as session:
            try:
                result = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).options(
                    load_only(UnitTestGenerationAttempt.id,
                              UnitTestGenerationAttempt.run_time,
                              UnitTestGenerationAttempt.generated_test,
                              UnitTestGenerationAttempt.imports,
                              UnitTestGenerationAttempt.stdout,
                              UnitTestGenerationAttempt.stderr,
                              UnitTestGenerationAttempt.llm_info)
                ).one().__dict__
                llm_info = result.pop('llm_info', {})
                if isinstance(llm_info, dict):
                    result.update(llm_info)
                return result
            except NoResultFound:
                return None

# Usage example:
# db = UnitTestDB('sqlite:///test_runs.db')
# db.insert_attempt(datetime.utcnow(), {"model": "gpt-4"}, {"prompt": "test"}, "generated_test
