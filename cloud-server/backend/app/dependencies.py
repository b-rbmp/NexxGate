from sqlalchemy.orm import Session
from typing import Generator
from app.db.db import SessionLocal

# Creates a connection to the database independently in each request. Closes the connection at the end of each request
def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
        

# Creates a connection to the database independently in each request. Does not close the connection at the end of each request
def get_db_standalone() -> Session:
    try:
        db = SessionLocal()
        return db
    except Exception as e:
        print("Error: " + e)