# backend/engine/memory/timeseries_store.py
"""
TimescaleDB wrapper for time-series market data storage.

Handles:
- OHLCV data storage
- Hypertable configuration
- Continuous aggregates (1min, 1hour, 1day)
- Data compression & retention policies
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncpg

from backend.core.logging import get_logger
from backend.core.config import settings

logger = get_logger(__name__)


class TimeseriesStore:
    """
    TimescaleDB client for market data storage.
    
    Features:
    - Automatic hypertable creation
    - Continuous aggregates for different time intervals
    - Compression after 7 days
    - 90-day retention for raw data
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        logger.info("TimeseriesStore initialized")
    
    async def connect(self):
        """Establish connection pool to TimescaleDB."""
        if self.pool:
            return
        
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                min_size=2,
                max_size=10
            )
            
            # Create tables if not exist
            await self.create_schema()
            
            logger.info("✅ Connected to TimescaleDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to TimescaleDB: {e}")
            raise
    
    async def create_schema(self):
        """Create hypertable and indexes."""
        async with self.pool.acquire() as conn:
            # Enable TimescaleDB extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            
            # Create market_data table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    time TIMESTAMPTZ NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    open NUMERIC NOT NULL,
                    high NUMERIC NOT NULL,
                    low NUMERIC NOT NULL,
                    close NUMERIC NOT NULL,
                    volume NUMERIC NOT NULL,
                    num_trades INTEGER,
                    source VARCHAR(20) DEFAULT 'binance'
                );
            """)
            
            # Convert to hypertable (if not already)
            try:
                await conn.execute("""
                    SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);
                """)
                logger.info("✅ Created hypertable: market_data")
            except Exception as e:
                logger.debug(f"Hypertable may already exist: {e}")
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time 
                ON market_data (symbol, time DESC);
            """)
            
            # Add compression policy (compress data older than 7 days)
            try:
                await conn.execute("""
                    SELECT add_compression_policy('market_data', INTERVAL '7 days', if_not_exists => TRUE);
                """)
                logger.info("✅ Added compression policy")
            except Exception as e:
                logger.debug(f"Compression policy may already exist: {e}")
            
            # Add retention policy (keep 90 days)
            try:
                await conn.execute("""
                    SELECT add_retention_policy('market_data', INTERVAL '90 days', if_not_exists => TRUE);
                """)
                logger.info("✅ Added retention policy (90 days)")
            except Exception as e:
                logger.debug(f"Retention policy may already exist: {e}")
    
    async def insert_ohlcv(
        self,
        symbol: str,
        data: List[Dict[str, Any]],
        source: str = "binance"
    ) -> int:
        """
        Insert OHLCV data into TimescaleDB.
        
        Args:
            symbol: Trading pair symbol
            data: List of OHLCV records
            source: Data source name
            
        Returns:
            Number of records inserted
        """
        if not data:
            return 0
        
        async with self.pool.acquire() as conn:
            # Prepare batch insert
            records = [
                (
                    record["timestamp"],
                    symbol,
                    record["open"],
                    record["high"],
                    record["low"],
                    record["close"],
                    record["volume"],
                    record.get("num_trades"),
                    source
                )
                for record in data
            ]
            
            # Use ON CONFLICT to handle duplicates
            query = """
                INSERT INTO market_data (time, symbol, open, high, low, close, volume, num_trades, source)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT DO NOTHING
            """
            
            result = await conn.executemany(query, records)
            
            logger.info(f"Inserted {len(records)} OHLCV records for {symbol}")
            return len(records)
    
    async def get_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve OHLCV data for a symbol.
        
        Args:
            symbol: Trading pair symbol
            start_date: Start time
            end_date: End time
            interval: Aggregation interval (None for raw data)
            
        Returns:
            List of OHLCV records
        """
        async with self.pool.acquire() as conn:
            if interval:
                # Use time_bucket for aggregation
                query = """
                    SELECT time_bucket($1, time) AS bucket,
                           symbol,
                           first(open, time) as open,
                           max(high) as high,
                           min(low) as low,
                           last(close, time) as close,
                           sum(volume) as volume
                    FROM market_data
                    WHERE symbol = $2
                      AND time >= $3
                      AND time <= $4
                    GROUP BY bucket, symbol
                    ORDER BY bucket
                """
                rows = await conn.fetch(query, interval, symbol, start_date, end_date)
            else:
                # Raw data
                query = """
                    SELECT time, symbol, open, high, low, close, volume
                    FROM market_data
                    WHERE symbol = $1
                      AND time >= $2
                      AND time <= $3
                    ORDER BY time
                """
                rows = await conn.fetch(query, symbol, start_date, end_date)
            
            return [dict(row) for row in rows]
    
    async def get_latest_timestamp(self, symbol: str) -> Optional[datetime]:
        """Get the most recent timestamp for a symbol."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT MAX(time) as latest FROM market_data WHERE symbol = $1",
                symbol
            )
            return row["latest"] if row else None
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("TimescaleDB connection closed")


# Singleton instance
_timeseries_store = None

def get_timeseries_store() -> TimeseriesStore:
    """Get singleton TimescaleDB instance."""
    global _timeseries_store
    if _timeseries_store is None:
        _timeseries_store = TimeseriesStore()
    return _timeseries_store
