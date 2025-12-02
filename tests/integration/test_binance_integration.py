# tests/integration/test_binance_integration.py
"""
Integration test for Binance connector.
Tests actual connectivity (not mocked).
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from backend.engine.feeds.binance_connector import BinanceConnector


async def test_binance_connection():
    """Test Binance API connectivity."""
    connector = BinanceConnector()
    
    # Test 1: Validate connection
    is_healthy = await connector.validate_connection()
    print(f"✅ Binance connection: {'Healthy' if is_healthy else 'Failed'}")
    assert is_healthy, "Binance API is not accessible"
    
    # Test 2: Fetch current price
    price = await connector.fetch_current_price("BTCUSDT")
    print(f"✅ Current BTC price: ${price:,.2f}")
    assert price is not None, "Failed to fetch current price"
    assert price > 0, "Invalid price returned"
    
    # Test 3: Fetch small amount of historical data
    print("\n🔄 Fetching 24 hours of BTC historical data...")
    data = await connector.fetch_ohlcv(
        symbol="BTCUSDT",
        interval="1h",
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow(),
        limit=24
    )
    
    print(f"✅ Fetched {len(data)} candles")
    assert len(data) > 0, "No OHLCV data returned"
    assert len(data) <= 24, "Returned more data than expected"
    
    # Verify data structure
    first_candle = data[0]
    assert "timestamp" in first_candle
    assert "open" in first_candle
    assert "high" in first_candle
    assert "low" in first_candle
    assert "close" in first_candle
    assert "volume" in first_candle
    
    print(f"✅ First candle: {first_candle['timestamp']} - OHLC: ${first_candle['open']:.2f} / ${first_candle['high']:.2f} / ${first_candle['low']:.2f} / ${first_candle['close']:.2f}")
    
    # Test 4: Fetch multiple symbols
    print("\n🔄 Fetching data for multiple symbols...")
    multi_data = await connector.fetch_multiple_symbols(
        symbols=["BTCUSDT", "ETHUSDT"],
        interval="1h",
        days=1
    )
    
    print(f"✅ Fetched data for {len(multi_data)} symbols")
    assert "BTCUSDT" in multi_data
    assert "ETHUSDT" in multi_data
    assert len(multi_data["BTCUSDT"]) > 0
    assert len(multi_data["ETHUSDT"]) > 0
    
    print("\n✅ All Binance connector tests passed!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Binance Connector Integration")
    print("=" * 60)
    
    result = asyncio.run(test_binance_connection())
    
    if result:
        print("\n" + "=" * 60)
        print("✅ SUCCESS: Binance connector is fully functional!")
        print("=" * 60)
