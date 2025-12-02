# backend/routes/market.py
"""
Market data API endpoints.

Provides:
- Binance historical OHLCV sync
- Market data queries
- Price lookups
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.engine.feeds import BinanceConnector
from backend.engine.memory.timeseries_store import get_timeseries_store
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/market", tags=["Market Data"])

# Singleton instances
binance = BinanceConnector()
timeseries = get_timeseries_store()


# === Pydantic Schemas ===

class BinanceSyncRequest(BaseModel):
    """Request for Binance data sync"""
    symbols: List[str] = Field(..., description="Trading pairs (e.g., ['BTCUSDT', 'ETHUSDT'])")
    interval: str = Field(default="1h", description="Candlestick interval (1m, 5m, 1h, 1d, etc.)")
    days: int = Field(default=30, description="Number of days of historical data", ge=1, le=365)


class BinanceSyncResponse(BaseModel):
    """Response from Binance sync"""
    success: bool
    symbols_synced: int
    total_records: int
    failed_symbols: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class OHLCVRecord(BaseModel):
    """OHLCV data record"""
    time: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class OHLCVResponse(BaseModel):
    """Response with OHLCV data"""
    symbol: str
    interval: Optional[str]
    start_date: datetime
    end_date: datetime
    records: List[OHLCVRecord]
    count: int


# === API Endpoints ===

@router.post("/binance/sync", response_model=BinanceSyncResponse, status_code=status.HTTP_201_CREATED)
async def sync_binance_data(request: BinanceSyncRequest):
    """
    Sync historical OHLCV data from Binance.
    
    Fetches historical market data and stores in TimescaleDB.
    
    Example:
        ```json
        {
            "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            "interval": "1h",
            "days": 30
        }
        ```
    """
    try:
        # Ensure TimescaleDB is connected
        await timeseries.connect()
        
        total_records = 0
        synced_symbols = 0
        failed_symbols = []
        errors = []
        
        for symbol in request.symbols:
            try:
                logger.info(f"Syncing {symbol} - {request.days} days of {request.interval} data")
                
                # Fetch from Binance
                data = await binance.fetch_ohlcv(
                    symbol=symbol,
                    interval=request.interval,
                    start_date=datetime.utcnow() - timedelta(days=request.days),
                    end_date=datetime.utcnow()
                )
                
                if not data:
                    logger.warning(f"No data fetched for {symbol}")
                    failed_symbols.append(symbol)
                    errors.append(f"{symbol}: No data returned from Binance")
                    continue
                
                # Store in TimescaleDB
                inserted = await timeseries.insert_ohlcv(
                    symbol=symbol,
                    data=data,
                    source="binance"
                )
                
                total_records += inserted
                synced_symbols += 1
                
                logger.info(f"✅ Synced {inserted} records for {symbol}")
                
            except Exception as e:
                logger.error(f"Failed to sync {symbol}: {e}")
                failed_symbols.append(symbol)
                errors.append(f"{symbol}: {str(e)}")
        
        return BinanceSyncResponse(
            success=synced_symbols > 0,
            symbols_synced=synced_symbols,
            total_records=total_records,
            failed_symbols=failed_symbols,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Binance sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Binance sync failed: {str(e)}"
        )


@router.get("/ohlcv/{symbol}", response_model=OHLCVResponse)
async def get_ohlcv(
    symbol: str,
    start_date: Optional[datetime] = Query(None, description="Start timestamp"),
    end_date: Optional[datetime] = Query(None, description="End timestamp"),
    interval: Optional[str] = Query(None, description="Aggregation interval (e.g., '1 hour', '1 day')")
):
    """
    Retrieve OHLCV data for a symbol.
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        start_date: Start time (default: 7 days ago)
        end_date: End time (default: now)
        interval: Time bucket for aggregation (optional)
        
    Example:
        ```
        GET /v1/market/ohlcv/BTCUSDT?start_date=2024-11-01&end_date=2024-11-30&interval=1%20day
        ```
    """
    try:
        await timeseries.connect()
        
        # Default date range
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Fetch data
        data = await timeseries.get_ohlcv(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        return OHLCVResponse(
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            records=data,
            count=len(data)
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch OHLCV: {str(e)}"
        )


@router.get("/price/{symbol}")
async def get_current_price(symbol: str):
    """
    Get current price for a symbol from Binance.
    
    Example:
        ```
        GET /v1/market/price/BTCUSDT
        ```
    """
    try:
        price = await binance.fetch_current_price(symbol)
        
        if price is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Price not found for {symbol}"
            )
        
        return {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch price for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch price: {str(e)}"
        )


@router.get("/status")
async def get_market_data_status():
    """Get market data connector status."""
    binance_healthy = await binance.validate_connection()
    
    # Get TimescaleDB status
    try:
        await timeseries.connect()
        timescale_healthy = True
    except:
        timescale_healthy = False
    
    return {
        "connectors": {
            "binance": {
                "healthy": binance_healthy,
                "source": binance.source_name
            },
            "timescaledb": {
                "healthy": timescale_healthy,
                "type": "time-series storage"
            }
        }
    }
