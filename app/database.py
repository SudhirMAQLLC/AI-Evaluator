from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    assignment_type = Column(String, index=True)
    file_path = Column(String)
    total_score = Column(Float, default=0.0)
    max_score = Column(Float, default=100.0)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, index=True)
    component_name = Column(String)
    score = Column(Float)
    max_score = Column(Float)
    feedback = Column(Text)
    status = Column(String)  # passed, failed, partial
    details = Column(Text, nullable=True)  # JSON string with detailed results

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 