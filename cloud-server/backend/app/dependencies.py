from sqlalchemy.orm import Session
from typing import Generator
from app.db.db import SessionLocal

def get_db() -> Generator:
    """
    Returns a generator that yields a database session.

    The generator is used as a dependency in FastAPI routes to provide a database session
    to the route function. The session is closed automatically when the route execution is
    finished.

    Yields:
        SessionLocal: A database session.

    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
        

def get_db_standalone() -> Session:
    """
    Get a standalone database session. (Used with MQTT)

    Returns:
        Session: A database session object.

    Raises:
        Exception: If there is an error creating the database session.
    """
    try:
        db = SessionLocal()
        return db
    except Exception as e:
        print("Error: " + e)