from sqlmodel import Session, create_engine, SQLModel
from config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency for getting database session"""
    with Session(engine) as session:
        yield session
