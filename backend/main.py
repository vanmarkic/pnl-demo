"""
PnL Demo API - Main Application Entry Point

This FastAPI application demonstrates:
- Energy trading contract management
- Trade execution and tracking
- P&L (Profit & Loss) calculation
- Risk metrics (VaR, Delta)
- AWS S3 integration for data storage

Learning points:
- FastAPI application structure
- Router organization
- Middleware configuration
- Database initialization
- Configuration management
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from models.base import engine, Base
from routers import contracts_router, trades_router, pnl_router, risk_router
from routers.data import router as data_router
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - runs on startup and shutdown.

    Creates database tables on startup.
    In production, use Alembic migrations instead.
    """
    settings = get_settings()

    # Startup
    logger.info(f"Starting application in {settings.environment} mode")

    # Create database tables (use migrations in production)
    if settings.environment == "development":
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    else:
        logger.info("Skipping auto table creation (use Alembic migrations)")

    yield

    # Shutdown
    logger.info("Application shutting down")


# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="PnL Demo API",
    description="""
    ## Energy Trading P&L Management System

    This API demonstrates a complete energy trading backend with:

    ### Features
    * **Contract Management** - Create and manage energy supply contracts
    * **Trade Execution** - Record buy/sell trades for gas and electricity
    * **P&L Tracking** - Calculate daily profit and loss
    * **Risk Metrics** - VaR, position delta, and stress testing
    * **Data Storage** - AWS S3 integration for market data

    ### Technologies
    * FastAPI for REST API
    * SQLAlchemy ORM with PostgreSQL
    * Alembic for database migrations
    * Pandas/NumPy for calculations
    * Pydantic for validation
    * AWS S3 for data storage
    * Docker & Kubernetes for deployment
    * Terraform for infrastructure

    ### Domain Concepts
    * **Contract**: Agreement to buy/sell energy at specified terms
    * **Trade**: Individual transaction within a contract
    * **Position**: Net exposure from all trades
    * **MTM**: Mark-to-Market valuation at current prices
    * **VaR**: Value at Risk - potential loss estimate
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contracts_router)
app.include_router(trades_router)
app.include_router(pnl_router)
app.include_router(risk_router)
app.include_router(data_router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to PnL Demo API",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs",
        "endpoints": {
            "contracts": "/api/contracts",
            "trades": "/api/trades",
            "pnl": "/api/pnl",
            "risk": "/api/risk",
            "data": "/api/data",
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "pnl-demo-api",
        "environment": settings.environment
    }


@app.post("/api/seed")
async def seed_database():
    """
    Seed the database with sample data for testing.

    Creates sample contracts, trades, and price data.
    """
    from models.base import SessionLocal
    from utils.seed_data import seed_all

    db = SessionLocal()
    try:
        result = seed_all(db)
        return {"message": "Database seeded successfully", "data": result}
    finally:
        db.close()


@app.get("/api/config")
async def get_config():
    """
    Get non-sensitive configuration info.

    Useful for debugging deployment issues.
    """
    return {
        "environment": settings.environment,
        "database_type": "postgresql" if "postgresql" in settings.database_url else "sqlite",
        "aws_region": settings.aws_region,
        "s3_bucket": settings.s3_bucket_name,
        "cors_origins": settings.cors_origins_list,
    }
