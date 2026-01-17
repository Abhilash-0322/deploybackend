"""
Price API routes for cryptocurrency data.
Uses CoinGecko API for real-time price data.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
import httpx
from pydantic import BaseModel

router = APIRouter(prefix="/prices", tags=["prices"])

# CoinGecko API base URL (free tier)
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Supported tokens with their CoinGecko IDs
SUPPORTED_TOKENS = {
    "APT": {"id": "aptos", "name": "Aptos", "symbol": "APT", "chain": "aptos"},
    "BTC": {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC", "chain": "bitcoin"},
    "ETH": {"id": "ethereum", "name": "Ethereum", "symbol": "ETH", "chain": "ethereum"},
    "SOL": {"id": "solana", "name": "Solana", "symbol": "SOL", "chain": "solana"},
    "BNB": {"id": "binancecoin", "name": "BNB", "symbol": "BNB", "chain": "bsc"},
    "AVAX": {"id": "avalanche-2", "name": "Avalanche", "symbol": "AVAX", "chain": "avalanche"},
    "MATIC": {"id": "matic-network", "name": "Polygon", "symbol": "MATIC", "chain": "polygon"},
    "ARB": {"id": "arbitrum", "name": "Arbitrum", "symbol": "ARB", "chain": "arbitrum"},
    "OP": {"id": "optimism", "name": "Optimism", "symbol": "OP", "chain": "optimism"},
    "SUI": {"id": "sui", "name": "Sui", "symbol": "SUI", "chain": "sui"},
    "DOGE": {"id": "dogecoin", "name": "Dogecoin", "symbol": "DOGE", "chain": "dogecoin"},
    "XRP": {"id": "ripple", "name": "XRP", "symbol": "XRP", "chain": "xrp"},
    "ADA": {"id": "cardano", "name": "Cardano", "symbol": "ADA", "chain": "cardano"},
    "LINK": {"id": "chainlink", "name": "Chainlink", "symbol": "LINK", "chain": "ethereum"},
    "UNI": {"id": "uniswap", "name": "Uniswap", "symbol": "UNI", "chain": "ethereum"},
}

# Cache for price data
price_cache: Dict[str, Any] = {}
cache_ttl = 30  # seconds


class TokenPrice(BaseModel):
    symbol: str
    name: str
    price: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap: float
    volume_24h: float
    high_24h: float
    low_24h: float
    last_updated: str


class MarketData(BaseModel):
    tokens: List[TokenPrice]
    global_market_cap: float
    total_volume_24h: float
    btc_dominance: float
    last_updated: str


class OHLCData(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float


class ChartData(BaseModel):
    symbol: str
    timeframe: str
    data: List[OHLCData]


async def fetch_with_retry(url: str, params: dict = None, retries: int = 3) -> dict:
    """Fetch data with retry logic."""
    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                response = await client.get(url, params=params, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    await asyncio.sleep(2 ** attempt)
                else:
                    response.raise_for_status()
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                await asyncio.sleep(1)
    return {}


@router.get("/tokens", response_model=MarketData)
async def get_all_token_prices():
    """Get current prices for all supported tokens."""
    cache_key = "all_tokens"
    
    # Check cache
    if cache_key in price_cache:
        cached = price_cache[cache_key]
        if (datetime.now() - cached["timestamp"]).seconds < cache_ttl:
            return cached["data"]
    
    try:
        # Get token IDs
        ids = ",".join([t["id"] for t in SUPPORTED_TOKENS.values()])
        
        # Fetch from CoinGecko
        url = f"{COINGECKO_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ids,
            "order": "market_cap_desc",
            "sparkline": "false",
            "price_change_percentage": "24h"
        }
        
        data = await fetch_with_retry(url, params)
        
        tokens = []
        for item in data:
            token_info = next(
                (t for t in SUPPORTED_TOKENS.values() if t["id"] == item["id"]),
                None
            )
            if token_info:
                tokens.append(TokenPrice(
                    symbol=token_info["symbol"],
                    name=item["name"],
                    price=item.get("current_price", 0) or 0,
                    price_change_24h=item.get("price_change_24h", 0) or 0,
                    price_change_percentage_24h=item.get("price_change_percentage_24h", 0) or 0,
                    market_cap=item.get("market_cap", 0) or 0,
                    volume_24h=item.get("total_volume", 0) or 0,
                    high_24h=item.get("high_24h", 0) or 0,
                    low_24h=item.get("low_24h", 0) or 0,
                    last_updated=item.get("last_updated", datetime.now().isoformat())
                ))
        
        # Get global data
        global_url = f"{COINGECKO_BASE}/global"
        global_data = await fetch_with_retry(global_url)
        global_info = global_data.get("data", {})
        
        result = MarketData(
            tokens=tokens,
            global_market_cap=global_info.get("total_market_cap", {}).get("usd", 0),
            total_volume_24h=global_info.get("total_volume", {}).get("usd", 0),
            btc_dominance=global_info.get("market_cap_percentage", {}).get("btc", 0),
            last_updated=datetime.now().isoformat()
        )
        
        # Update cache
        price_cache[cache_key] = {
            "data": result,
            "timestamp": datetime.now()
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch prices: {str(e)}")


@router.get("/token/{symbol}", response_model=TokenPrice)
async def get_token_price(symbol: str):
    """Get current price for a specific token."""
    symbol = symbol.upper()
    
    if symbol not in SUPPORTED_TOKENS:
        raise HTTPException(status_code=404, detail=f"Token {symbol} not supported")
    
    cache_key = f"token_{symbol}"
    
    # Check cache
    if cache_key in price_cache:
        cached = price_cache[cache_key]
        if (datetime.now() - cached["timestamp"]).seconds < cache_ttl:
            return cached["data"]
    
    try:
        token_info = SUPPORTED_TOKENS[symbol]
        url = f"{COINGECKO_BASE}/coins/{token_info['id']}"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        }
        
        data = await fetch_with_retry(url, params)
        market_data = data.get("market_data", {})
        
        result = TokenPrice(
            symbol=symbol,
            name=data.get("name", token_info["name"]),
            price=market_data.get("current_price", {}).get("usd", 0),
            price_change_24h=market_data.get("price_change_24h", 0) or 0,
            price_change_percentage_24h=market_data.get("price_change_percentage_24h", 0) or 0,
            market_cap=market_data.get("market_cap", {}).get("usd", 0),
            volume_24h=market_data.get("total_volume", {}).get("usd", 0),
            high_24h=market_data.get("high_24h", {}).get("usd", 0),
            low_24h=market_data.get("low_24h", {}).get("usd", 0),
            last_updated=data.get("last_updated", datetime.now().isoformat())
        )
        
        # Update cache
        price_cache[cache_key] = {
            "data": result,
            "timestamp": datetime.now()
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price: {str(e)}")


@router.get("/chart/{symbol}", response_model=ChartData)
async def get_chart_data(
    symbol: str,
    timeframe: str = Query("1d", regex="^(1h|4h|1d|1w|1m)$")
):
    """Get OHLC chart data for a token."""
    symbol = symbol.upper()
    
    if symbol not in SUPPORTED_TOKENS:
        raise HTTPException(status_code=404, detail=f"Token {symbol} not supported")
    
    cache_key = f"chart_{symbol}_{timeframe}"
    
    # Check cache (longer TTL for chart data)
    if cache_key in price_cache:
        cached = price_cache[cache_key]
        if (datetime.now() - cached["timestamp"]).seconds < 60:
            return cached["data"]
    
    try:
        token_info = SUPPORTED_TOKENS[symbol]
        
        # Map timeframe to days
        days_map = {"1h": 1, "4h": 1, "1d": 30, "1w": 90, "1m": 365}
        days = days_map.get(timeframe, 30)
        
        url = f"{COINGECKO_BASE}/coins/{token_info['id']}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": days
        }
        
        data = await fetch_with_retry(url, params)
        
        ohlc_data = [
            OHLCData(
                timestamp=item[0],
                open=item[1],
                high=item[2],
                low=item[3],
                close=item[4]
            )
            for item in data
        ]
        
        result = ChartData(
            symbol=symbol,
            timeframe=timeframe,
            data=ohlc_data
        )
        
        # Update cache
        price_cache[cache_key] = {
            "data": result,
            "timestamp": datetime.now()
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chart data: {str(e)}")


@router.get("/history/{symbol}")
async def get_price_history(
    symbol: str,
    days: int = Query(7, ge=1, le=365)
):
    """Get price history for a token."""
    symbol = symbol.upper()
    
    if symbol not in SUPPORTED_TOKENS:
        raise HTTPException(status_code=404, detail=f"Token {symbol} not supported")
    
    try:
        token_info = SUPPORTED_TOKENS[symbol]
        url = f"{COINGECKO_BASE}/coins/{token_info['id']}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days
        }
        
        data = await fetch_with_retry(url, params)
        
        return {
            "symbol": symbol,
            "days": days,
            "prices": [
                {"timestamp": p[0], "price": p[1]}
                for p in data.get("prices", [])
            ],
            "volumes": [
                {"timestamp": v[0], "volume": v[1]}
                for v in data.get("total_volumes", [])
            ],
            "market_caps": [
                {"timestamp": m[0], "market_cap": m[1]}
                for m in data.get("market_caps", [])
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.get("/trending")
async def get_trending_coins():
    """Get trending coins from CoinGecko."""
    cache_key = "trending"
    
    # Check cache
    if cache_key in price_cache:
        cached = price_cache[cache_key]
        if (datetime.now() - cached["timestamp"]).seconds < 300:  # 5 min cache
            return cached["data"]
    
    try:
        url = f"{COINGECKO_BASE}/search/trending"
        data = await fetch_with_retry(url)
        
        trending = []
        for coin in data.get("coins", [])[:10]:
            item = coin.get("item", {})
            trending.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "symbol": item.get("symbol"),
                "market_cap_rank": item.get("market_cap_rank"),
                "thumb": item.get("thumb"),
                "price_btc": item.get("price_btc", 0)
            })
        
        result = {
            "coins": trending,
            "last_updated": datetime.now().isoformat()
        }
        
        # Update cache
        price_cache[cache_key] = {
            "data": result,
            "timestamp": datetime.now()
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending: {str(e)}")


@router.get("/supported")
async def get_supported_tokens():
    """Get list of supported tokens."""
    return {
        "tokens": [
            {
                "symbol": info["symbol"],
                "name": info["name"],
                "chain": info["chain"],
                "coingecko_id": info["id"]
            }
            for info in SUPPORTED_TOKENS.values()
        ]
    }
