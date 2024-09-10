from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, load_only
from sqlalchemy.orm.exc import NoResultFound

Base = declarative_base()


class UnitTestGenerationAttempt(Base):
    __tablename__ = "unit_test_generation_attempts"
    id = Column(Integer, primary_key=True)
    run_time = Column(DateTime, default=datetime.now)  # Use local time
    status = Column(String)
    reason = Column(Text)
    exit_code = Column(Integer)
    stderr = Column(Text)
    stdout = Column(Text)
    test_code = Column(Text)
    imports = Column(Text)
    original_test_file = Column(Text)
    processed_test_file = Column(Text)


class UnitTestDB:
    def __init__(self, db_connection_string):
        self.engine = create_engine(db_connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def insert_attempt(self, test_result: dict):
        with self.Session() as session:
            new_attempt = UnitTestGenerationAttempt(
                run_time=datetime.now(),  # Use local time
                status=test_result.get("status"),
                reason=test_result.get("reason"),
                exit_code=test_result.get("exit_code"),
                stderr=test_result.get("stderr"),
                stdout=test_result.get("stdout"),
                test_code=test_result.get("test", {}).get("test_code", ""),
                imports=test_result.get("test", {}).get("new_imports_code", ""),
                original_test_file=test_result.get("original_test_file"),
                processed_test_file=test_result.get("processed_test_file"),
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
                return (
                    session.query(UnitTestGenerationAttempt)
                    .filter_by(id=attempt_id)
                    .one()
                )
            except NoResultFound:
                return None

    def select_attempt_in_range(self, start: datetime, end: datetime):
        with self.Session() as session:
            return (
                session.query(UnitTestGenerationAttempt)
                .filter(
                    UnitTestGenerationAttempt.run_time >= start,
                    UnitTestGenerationAttempt.run_time <= end,
                )
                .all()
            )

    def select_attempt_flat(self, attempt_id):
        with self.Session() as session:
            try:
                result = (
                    session.query(UnitTestGenerationAttempt)
                    .filter_by(id=attempt_id)
                    .options(
                        load_only(
                            UnitTestGenerationAttempt.id,
                            UnitTestGenerationAttempt.run_time,
                            UnitTestGenerationAttempt.status,
                            UnitTestGenerationAttempt.reason,
                            UnitTestGenerationAttempt.exit_code,
                            UnitTestGenerationAttempt.stderr,
                            UnitTestGenerationAttempt.stdout,
                            UnitTestGenerationAttempt.test_code,
                            UnitTestGenerationAttempt.imports,
                            UnitTestGenerationAttempt.original_test_file,
                            UnitTestGenerationAttempt.processed_test_file,
                        )
                    )
                    .one()
                    .__dict__
                )
                return result
            except NoResultFound:
                return None
