from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from backend.config import DATABASE_URL


# Create a SQLAlchemy engine that manages connections to the database.
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
def get_db():
    db = SessionLocal()
    print(f"Connected to: {db.bind.url.database}")
    try:
        yield db
    finally:
        db.close()

