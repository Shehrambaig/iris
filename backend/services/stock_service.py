"""
Stock Service - Yahoo Finance Integration
Provides real-time and historical stock data
"""

import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime


class StockService:
    def __init__(self):
        # Symbol mapping for indices
        self.index_map = {
            "SPX": "^GSPC",
            "NDQ": "^IXIC",
            "DJI": "^DJI",
            "VIX": "^VIX",
            "DXY": "DX-Y.NYB",
        }

    async def get_stock_data(self, symbol: str) -> Dict:
        """Get real-time stock data for a symbol using ticker.info (avoids rate limiting)"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Use info property which uses a different API endpoint
            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose", 0)
            open_price = info.get("regularMarketOpen") or info.get("open") or current_price
            high_price = info.get("dayHigh") or info.get("regularMarketDayHigh") or current_price
            low_price = info.get("dayLow") or info.get("regularMarketDayLow") or current_price
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or current_price
            volume = info.get("volume") or info.get("regularMarketVolume") or 0
            name = info.get("longName") or info.get("shortName") or symbol

            # Calculate change
            change = current_price - prev_close
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0

            return {
                "symbol": symbol,
                "name": name,
                "price": float(current_price),
                "open": float(open_price),
                "high": float(high_price),
                "low": float(low_price),
                "close": float(current_price),
                "volume": int(volume),
                "change": float(change),
                "changePercent": float(change_percent),
                "timestamp": int(datetime.now().timestamp())
            }
        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {e}")
            raise

    async def get_multiple_stocks(self, symbols: List[str]) -> List[Dict]:
        """Get real-time data for multiple stocks"""
        import asyncio
        results = []
        for i, symbol in enumerate(symbols):
            try:
                data = await self.get_stock_data(symbol)
                results.append(data)
                # Add small delay between requests to avoid rate limiting (except for last item)
                if i < len(symbols) - 1:
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue

        return results

    async def get_index_data(self, symbol: str) -> Dict:
        """Get real-time index data using ticker.info (avoids rate limiting)"""
        try:
            # Map to Yahoo Finance symbol
            yf_symbol = self.index_map.get(symbol, symbol)

            ticker = yf.Ticker(yf_symbol)
            info = ticker.info

            # Use info property which uses a different API endpoint
            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose", 0)
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or current_price

            # Calculate change
            change = current_price - prev_close
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0

            return {
                "symbol": symbol,
                "name": symbol,
                "price": float(current_price),
                "change": float(change),
                "changePercent": float(change_percent),
                "timestamp": int(datetime.now().timestamp())
            }
        except Exception as e:
            print(f"Error fetching index data for {symbol}: {e}")
            raise

    async def get_candle_data(self, symbol: str, period: str = "6mo", interval: str = "1d") -> List[Dict]:
        """Get historical candlestick data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                raise Exception(f"No historical data found for {symbol}")

            candles = []
            for idx, row in hist.iterrows():
                candles.append({
                    "time": int(idx.timestamp()),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                })

            return candles
        except Exception as e:
            print(f"Error fetching candle data for {symbol}: {e}")
            raise
