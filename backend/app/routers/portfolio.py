from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
from app.database import get_db
from app.models.holding import Holding
from app.schemas.portfolio import (
    HoldingCreate, HoldingUpdate, HoldingResponse, PortfolioResponse,
)
from app.services.yfinance_service import yf_service

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    quotes = await asyncio.gather(*[yf_service.get_quote(h.ticker) for h in holdings], return_exceptions=True)

    holding_responses = []
    total_value = 0.0
    total_cost = 0.0
    day_pnl = 0.0

    for h, quote_or_exc in zip(holdings, quotes):
        quote = quote_or_exc if not isinstance(quote_or_exc, Exception) else None
        current_price = quote.price if quote else h.avg_cost
        mv = h.market_value(current_price)
        pnl = h.pnl(current_price)
        pnl_pct = h.pnl_pct(current_price)

        holding_responses.append(HoldingResponse(
            id=h.id,
            ticker=h.ticker,
            name=h.name,
            quantity=h.quantity,
            avg_cost=h.avg_cost,
            purchase_date=h.purchase_date,
            current_price=current_price,
            market_value=mv,
            pnl=pnl,
            pnl_pct=pnl_pct,
            created_at=h.created_at,
        ))
        total_value += mv
        total_cost += h.avg_cost * h.quantity
        if quote:
            day_pnl += quote.change * h.quantity

    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0

    return PortfolioResponse(
        holdings=holding_responses,
        total_value=total_value,
        total_cost=total_cost,
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
        day_pnl=day_pnl,
    )


@router.post("/holding", response_model=HoldingResponse)
async def create_holding(data: HoldingCreate, db: AsyncSession = Depends(get_db)):
    quote = await yf_service.get_quote(data.ticker)
    if not quote:
        raise HTTPException(status_code=400, detail="Invalid ticker")
    holding = Holding(
        ticker=data.ticker.upper(),
        name=quote.name,
        quantity=data.quantity,
        avg_cost=data.avg_cost,
        purchase_date=data.purchase_date,
    )
    db.add(holding)
    await db.commit()
    await db.refresh(holding)

    current_price = quote.price
    return HoldingResponse(
        id=holding.id,
        ticker=holding.ticker,
        name=holding.name,
        quantity=holding.quantity,
        avg_cost=holding.avg_cost,
        purchase_date=holding.purchase_date,
        current_price=current_price,
        market_value=holding.market_value(current_price),
        pnl=holding.pnl(current_price),
        pnl_pct=holding.pnl_pct(current_price),
        created_at=holding.created_at,
    )


@router.put("/holding/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    holding_id: int, data: HoldingUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Holding).where(Holding.id == holding_id))
    holding = result.scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    if data.quantity is not None:
        holding.quantity = data.quantity
    if data.avg_cost is not None:
        holding.avg_cost = data.avg_cost

    await db.commit()
    await db.refresh(holding)

    quote = await yf_service.get_quote(holding.ticker)
    current_price = quote.price if quote else holding.avg_cost
    return HoldingResponse(
        id=holding.id,
        ticker=holding.ticker,
        name=holding.name,
        quantity=holding.quantity,
        avg_cost=holding.avg_cost,
        purchase_date=holding.purchase_date,
        current_price=current_price,
        market_value=holding.market_value(current_price),
        pnl=holding.pnl(current_price),
        pnl_pct=holding.pnl_pct(current_price),
        created_at=holding.created_at,
    )


@router.delete("/holding/{holding_id}")
async def delete_holding(holding_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Holding).where(Holding.id == holding_id))
    holding = result.scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    await db.delete(holding)
    await db.commit()
    return {"success": True}
