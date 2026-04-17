import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv(verbose=False)

DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy 2.0 style Base
class Base(DeclarativeBase):
    id = Column(Integer, primary_key=True, autoincrement=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
