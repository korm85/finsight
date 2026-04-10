from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.database import get_db
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.watchlist import (
    WatchlistCreate, WatchlistResponse, WatchlistItemCreate, WatchlistItemResponse,
)
from app.services.yfinance_service import yf_service

router = APIRouter(prefix="/api/watchlists", tags=["watchlists"])


@router.get("", response_model=List[WatchlistResponse])
async def get_watchlists(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Watchlist).options(selectinload(Watchlist.items)))
    watchlists = result.scalars().all()

    responses = []
    for w in watchlists:
        items_with_price = []
        for item in w.items:
            quote = await yf_service.get_quote(item.ticker)
            if quote:
                items_with_price.append(WatchlistItemResponse(
                    ticker=item.ticker,
                    name=item.name,
                    price=quote.price,
                    change_pct=quote.change_pct,
                ))
        responses.append(WatchlistResponse(
            id=w.id, name=w.name, items=items_with_price, created_at=w.created_at
        ))
    return responses


@router.post("", response_model=WatchlistResponse)
async def create_watchlist(data: WatchlistCreate, db: AsyncSession = Depends(get_db)):
    wl = Watchlist(name=data.name)
    db.add(wl)
    await db.commit()
    await db.refresh(wl)
    return WatchlistResponse(id=wl.id, name=wl.name, items=[], created_at=wl.created_at)


@router.post("/{watchlist_id}/items")
async def add_watchlist_item(
    watchlist_id: int, data: WatchlistItemCreate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    wl = result.scalar_one_or_none()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    item = WatchlistItem(
        watchlist_id=watchlist_id,
        ticker=data.ticker.upper(),
        name=data.name,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return await get_watchlists(db)


@router.delete("/{watchlist_id}/items/{ticker}")
async def remove_watchlist_item(
    watchlist_id: int, ticker: str, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.ticker == ticker.upper(),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.commit()
    return {"success": True}
