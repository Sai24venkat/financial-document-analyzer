from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import uuid

Base = declarative_base()

class AnalysisRequest(Base):
    __tablename__ = 'analysis_requests'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    query = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

engine = create_engine('sqlite:///financial_analyzer.db', connect_args={"check_same_thread": False}, pool_pre_ping=True)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
