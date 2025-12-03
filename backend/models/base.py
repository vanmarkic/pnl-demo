"""
Base model configuration for SQLAlchemy ORM.

Learning points:
- SQLAlchemy is the most popular Python ORM
- We use declarative_base() to create a base class for all models
- This allows us to define tables as Python classes
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URL - SQLite for development, easily switch to PostgreSQL
# PostgreSQL example: "postgresql://user:password@localhost:5432/pnl_demo"
DATABASE_URL = "sqlite:///./pnl_demo.db"

# Create engine - the connection to the database
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite specific
)

# Session factory - creates database sessions for transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency injection pattern for FastAPI.
    Yields a database session and ensures it's closed after use.

    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
