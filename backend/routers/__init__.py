# API Routers
# Each router handles a specific domain area

from .contracts import router as contracts_router
from .trades import router as trades_router
from .pnl import router as pnl_router
from .risk import router as risk_router
from .data import router as data_router
from .athena import router as athena_router

__all__ = [
    "contracts_router",
    "trades_router",
    "pnl_router",
    "risk_router",
    "data_router",
    "athena_router",
]
