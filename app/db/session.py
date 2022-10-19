from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_URL = "sqlite:///./ivern.db"

Engine = create_engine(DB_URL, connect_args={"check_same_thread": False, "timeout": 15})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
