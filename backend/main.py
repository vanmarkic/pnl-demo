"""
PnL Demo API - Main Application Entry Point

This FastAPI application demonstrates:
- Energy trading contract management
- Trade execution and tracking
- P&L (Profit & Loss) calculation
- Risk metrics (VaR, Delta)

Learning points:
- FastAPI application structure
- Router organization
- Middleware configuration
- Database initialization
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from models.base import engine, Base
from routers import contracts_router, trades_router, pnl_router, risk_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - runs on startup and shutdown.

    Creates database tables on startup.
    """
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
    yield
    # Shutdown: cleanup if needed
    print("Application shutting down")


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

    ### Technologies
    * FastAPI for REST API
    * SQLAlchemy ORM for database
    * Pandas/NumPy for calculations
    * Pydantic for validation

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
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React port
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contracts_router)
app.include_router(trades_router)
app.include_router(pnl_router)
app.include_router(risk_router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to PnL Demo API",
        "docs": "/docs",
        "endpoints": {
            "contracts": "/api/contracts",
            "trades": "/api/trades",
            "pnl": "/api/pnl",
            "risk": "/api/risk",
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "pnl-demo-api"}


# Optional: Seed data endpoint for development
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
