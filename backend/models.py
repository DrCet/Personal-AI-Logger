# backend/models.py
# This file defines the database models for the Personal AI Logger project using SQLAlchemy.
# Models represent the structure of the database tables and how data is stored and retrieved.

from sqlalchemy import Column, Integer, String, DateTime
from backend.database import Base

class Log(Base):
    # Defie the name of table in the database
    __tablename__ = "logs"
    # 'id' is the primary key for the logs table
    id = Column(Integer, primary_key=True, index=True)
    # 'text' is a column in the logs table that stores the text of the log
    text = Column(String(512))
    # aduio_file is a column in the logs table that stores the audio file name
    audio_file = Column(String(128))
    # timestamp is a column in the logs table that stores the timestamp
    timestamp = Column(DateTime)
