# backend/engine/feeds/binance_connector.py
"""
Binance API Connector for cryptocurrency market data.

Fetches:
- Historical OHLCV (Open, High, Low, Close, Volume)
- Real-time price data
- Multiple trading pairs (BTC-USD, ETH-USD, etc.)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import httpx

from .base import BaseFeedConnector
from backend.core.logging import get_logger
from backend.core.config import settings

logger = get_logger(__name__)


class BinanceConnector(BaseFeedConnector):
    """
    Binance API connector for cryptocurrency market data.
    
    Supports:
    - Historical OHLCV data
    - Multiple symbols (BTC, ETH, BNB, etc.)
    - Configurable time intervals (1m, 5m, 1h, 1d)
    - Rate limiting (1200 requests/min)
    """
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    # Interval mapping (Binance format)
    INTERVALS = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1w": "1w",
    }
    
    def __init__(self, source_name: str = "Binance"):
        super().__init__(source_name)
        self.timeout = 30
        self.rate_limit_delay = 0.05  # 50ms between requests (1200/min max)
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            interval: Candlestick interval (1m, 5m, 1h, 1d, etc.)
            start_date: Start time (default: 30 days ago)
            end_date: End time (default: now)
            limit: Max candles to fetch (default: 1000, max: 1000)
            
        Returns:
            List of OHLCV records
        """
        # Validate interval
        if interval not in self.INTERVALS:
            raise ValueError(f"Invalid interval: {interval}. Must be one of {list(self.INTERVALS.keys())}")
        
        # Default date range
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        all_data = []
        current_start = start_date
        
        # Binance limits to 1000 candles per request, so paginate
        while current_start < end_date:
            try:
                data = await self._fetch_single_batch(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start,
                    end_time=end_date,
                    limit=limit
                )
                
                if not data:
                    break
                
                all_data.extend(data)
                
                # Update start time for next batch
                last_timestamp = data[-1]["timestamp"]
                current_start = last_timestamp + timedelta(milliseconds=1)
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)
                
                logger.debug(f"Fetched {len(data)} candles for {symbol}")
                
            except Exception as e:
                logger.error(f"Failed to fetch batch for {symbol}: {e}")
                break
        
        logger.info(f"Fetched {len(all_data)} total candles for {symbol} from {start_date} to {end_date}")
        return all_data
    
    async def _fetch_single_batch(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch a single batch of OHLCV data."""
        params = {
            "symbol": symbol,
            "interval": self.INTERVALS[interval],
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
            "limit": min(limit, 1000)
        }
        
        url = f"{self.BASE_URL}/klines"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            raw_data = response.json()
            
            # Parse Binance format
            return self._parse_klines(raw_data)
    
    def _parse_klines(self, raw_data: List[List]) -> List[Dict[str, Any]]:
        """
        Parse Binance klines response.
        
        Binance format:
        [
            [
                1499040000000,      // Open time
                "0.01634790",       // Open
                "0.80000000",       // High
                "0.01575800",       // Low
                "0.01577100",       // Close
                "148976.11427815",  // Volume
                1499644799999,      // Close time
                "2434.19055334",    // Quote asset volume
                308,                // Number of trades
                "1756.87402397",    // Taker buy base asset volume
                "28.46694368",      // Taker buy quote asset volume
                "17928899.62484339" // Ignore
            ]
        ]
        """
        parsed = []
        
        for kline in raw_data:
            parsed.append({
                "timestamp": datetime.fromtimestamp(kline[0] / 1000),
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "close_timestamp": datetime.fromtimestamp(kline[6] / 1000),
                "num_trades": int(kline[8]),
            })
        
        return parsed
    
    async def fetch_multiple_symbols(
        self,
        symbols: List[str],
        interval: str = "1h",
        days: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch OHLCV data for multiple symbols.
        
        Args:
            symbols: List of trading pairs (e.g., ["BTCUSDT", "ETHUSDT"])
            interval: Candlestick interval
            days: Number of days of historical data
            
        Returns:
            Dict mapping symbol to OHLCV data
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()
        
        results = {}
        
        for symbol in symbols:
            try:
                data = await self.fetch_ohlcv(
                    symbol=symbol,
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date
                )
                results[symbol] = data
                
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                results[symbol] = []
        
        return results
    
    async def fetch_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch current price for a symbol.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            Current price or None
        """
        try:
            url = f"{self.BASE_URL}/ticker/price"
            params = {"symbol": symbol}
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return float(data["price"])
                
        except Exception as e:
            logger.error(f"Failed to fetch current price for {symbol}: {e}")
            return None
    
    async def validate_connection(self) -> bool:
        """Test Binance API connectivity."""
        try:
            url = f"{self.BASE_URL}/ping"
            
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                return response.status_code == 200
                
        except:
            return False
    
    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Base class implementation (not used directly).
        Use fetch_ohlcv() instead.
        """
        raise NotImplementedError("Use fetch_ohlcv() for Binance connector")
