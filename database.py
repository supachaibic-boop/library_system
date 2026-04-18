import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the directory where database.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "library.db")

# Priority 1: Use environment variable (Cloud/PostgreSQL)
# Priority 2: Use local SQLite (Development)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render and other cloud providers often use 'postgres://'
    # SQLAlchemy requires 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# Adjust engine settings based on DB type
engine_args = {}
if "sqlite" not in SQLALCHEMY_DATABASE_URL:
    # For PostgreSQL, we don't need check_same_thread
    pass
else:
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, **engine_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
