#!/usr/bin/env python3
"""
Test script to verify NASDAQ endpoint works
"""
import asyncio
from main import app, nasdaq_watchlist

async def test_nasdaq():
    print("Testing NASDAQ endpoint...")
    try:
        result = await nasdaq_watchlist()
        print("SUCCESS: NASDAQ endpoint works!")
        print(f"  Retrieved {len(result['data']['rows'])} stocks")
        for stock in result['data']['rows'][:3]:
            print(f"  - {stock['symbol']}: {stock['lastSale']}")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check route is registered
    routes = [r.path for r in app.routes if 'nasdaq' in r.path]
    print(f"NASDAQ routes registered: {routes}")

    # Test the endpoint
    success = asyncio.run(test_nasdaq())
    exit(0 if success else 1)
