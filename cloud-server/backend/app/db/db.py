from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

# Creation of the connection to the Database, gets a session to perform the actions

def get_db_url():
    """
    Returns the database URL based on the configuration settings.

    Returns:
        str: The database URL.
    """
    return "{dbservice}://{dbuser}:{dbpass}@{dbhost}/{dbname}".format(
        dbservice=settings.DB_SERVICE,
        dbuser=settings.DB_USER,
        dbpass=settings.DB_PASS,
        dbhost=settings.DB_HOST,
        dbname=settings.DB_NAME)

# Creates the SQL alchemy engine through the defined URL, with pool_pre_ping to avoid timeout errors
engine = create_engine(get_db_url(), connect_args={'options': f'-csearch_path={settings.DB_SCHEMA}'}, pool_pre_ping=True)

# Creates a session to make modifications with the engine. It will be used by db_manager.py for CRUD operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

