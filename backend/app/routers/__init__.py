from app.routers.market import router as market_router
from app.routers.portfolio import router as portfolio_router
from app.routers.watchlist import router as watchlist_router
from app.routers.alerts import router as alerts_router
from app.routers.settings import router as settings_router
from app.routers.analysis import router as analysis_router

__all__ = [
    "market_router", "portfolio_router", "watchlist_router",
    "alerts_router", "settings_router", "analysis_router",
]