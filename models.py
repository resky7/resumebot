from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, ForeignKey, DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
from config import DATABASE_URL

Base = declarative_base()

# Engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    lang = Column(String, default="ru")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resumes = relationship("Resume", back_populates="user")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    city = Column(String)
    position = Column(String)
    experience = Column(String)
    education = Column(String)
    skills = Column(Text)
    consent_for_employers = Column(Boolean, default=False)
    pdf_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="resumes")

class Employer(Base):
    __tablename__ = "employers"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String)
    email = Column(String)
    plan = Column(String, default="free")  # starter/pro/enterprise
    api_key = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
