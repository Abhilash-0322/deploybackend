'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Navbar } from '@/components/ui/Navbar';
import './trading.css';

// When served from same origin, use relative URLs
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

interface TokenPrice {
  symbol: string;
  name: string;
  price: number;
  price_change_24h: number;
  price_change_percentage_24h: number;
  market_cap: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
  last_updated: string;
}

interface MarketData {
  tokens: TokenPrice[];
  global_market_cap: number;
  total_volume_24h: number;
  btc_dominance: number;
  last_updated: string;
}

interface OHLCData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface OrderBookEntry {
  price: number;
  amount: number;
  total: number;
}

interface Trade {
  id: string;
  price: number;
  amount: number;
  side: 'buy' | 'sell';
  time: string;
}

export default function TradingPage() {
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [selectedToken, setSelectedToken] = useState<string>('APT');
  const [selectedTokenData, setSelectedTokenData] = useState<TokenPrice | null>(null);
  const [chartData, setChartData] = useState<OHLCData[]>([]);
  const [timeframe, setTimeframe] = useState<string>('1d');
  const [loading, setLoading] = useState(true);
  const [orderType, setOrderType] = useState<'limit' | 'market'>('limit');
  const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy');
  const [orderPrice, setOrderPrice] = useState<string>('');
  const [orderAmount, setOrderAmount] = useState<string>('');
  const [watchlist, setWatchlist] = useState<string[]>(['APT', 'BTC', 'ETH', 'SOL']);
  const [orderBook, setOrderBook] = useState<{ bids: OrderBookEntry[], asks: OrderBookEntry[] }>({ bids: [], asks: [] });
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [showMobileMenu, setShowMobileMenu] = useState<'chart' | 'orderbook' | 'trades' | 'order'>('chart');
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const tradingViewRef = useRef<any>(null);

  // Fetch market data
  const fetchMarketData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/prices/tokens`);
      if (res.ok) {
        const data = await res.json();
        setMarketData(data);

        // Update selected token data
        const token = data.tokens.find((t: TokenPrice) => t.symbol === selectedToken);
        if (token) {
          setSelectedTokenData(token);
          if (!orderPrice) {
            setOrderPrice(token.price.toFixed(2));
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch market data:', error);
    }
  }, [selectedToken, orderPrice]);

  // Fetch chart data
  const fetchChartData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/prices/chart/${selectedToken}?timeframe=${timeframe}`);
      if (res.ok) {
        const data = await res.json();
        setChartData(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch chart data:', error);
    }
  }, [selectedToken, timeframe]);

  // Generate mock order book based on current price
  const generateOrderBook = useCallback((price: number) => {
    const bids: OrderBookEntry[] = [];
    const asks: OrderBookEntry[] = [];

    for (let i = 0; i < 15; i++) {
      const bidPrice = price * (1 - (i + 1) * 0.001);
      const askPrice = price * (1 + (i + 1) * 0.001);
      const bidAmount = Math.random() * 100 + 10;
      const askAmount = Math.random() * 100 + 10;

      bids.push({
        price: bidPrice,
        amount: bidAmount,
        total: bids.reduce((sum, b) => sum + b.amount, 0) + bidAmount
      });

      asks.push({
        price: askPrice,
        amount: askAmount,
        total: asks.reduce((sum, a) => sum + a.amount, 0) + askAmount
      });
    }

    setOrderBook({ bids, asks: asks.reverse() });
  }, []);

  // Generate mock recent trades
  const generateRecentTrades = useCallback((price: number) => {
    const trades: Trade[] = [];
    const now = Date.now();

    for (let i = 0; i < 20; i++) {
      trades.push({
        id: `trade-${i}`,
        price: price * (1 + (Math.random() - 0.5) * 0.002),
        amount: Math.random() * 50 + 1,
        side: Math.random() > 0.5 ? 'buy' : 'sell',
        time: new Date(now - i * 30000).toLocaleTimeString()
      });
    }

    setRecentTrades(trades);
  }, []);

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchMarketData(), fetchChartData()]);
      setLoading(false);
    };
    loadData();
  }, []);

  // Refresh data periodically
  useEffect(() => {
    const interval = setInterval(() => {
      fetchMarketData();
    }, 10000); // Every 10 seconds

    return () => clearInterval(interval);
  }, [fetchMarketData]);

  // Update when token or timeframe changes
  useEffect(() => {
    fetchChartData();
  }, [selectedToken, timeframe, fetchChartData]);

  // Update order book and trades when token data changes
  useEffect(() => {
    if (selectedTokenData) {
      generateOrderBook(selectedTokenData.price);
      generateRecentTrades(selectedTokenData.price);
    }
  }, [selectedTokenData, generateOrderBook, generateRecentTrades]);

  // Initialize TradingView widget
  useEffect(() => {
    if (typeof window !== 'undefined' && chartContainerRef.current) {
      // Load TradingView script
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = () => {
        if ((window as any).TradingView && chartContainerRef.current) {
          tradingViewRef.current = new (window as any).TradingView.widget({
            autosize: true,
            symbol: `BINANCE:${selectedToken}USDT`,
            interval: timeframe === '1h' ? '60' : timeframe === '4h' ? '240' : timeframe === '1d' ? 'D' : timeframe === '1w' ? 'W' : 'M',
            timezone: 'Etc/UTC',
            theme: 'dark',
            style: '1',
            locale: 'en',
            toolbar_bg: '#0a0a0f',
            enable_publishing: false,
            hide_side_toolbar: false,
            allow_symbol_change: true,
            container_id: 'tradingview-chart',
            backgroundColor: '#0a0a0f',
            gridColor: 'rgba(0, 212, 170, 0.05)',
            studies: [
              'MAExp@tv-basicstudies',
              'RSI@tv-basicstudies',
              'MACD@tv-basicstudies'
            ]
          });
        }
      };
      document.head.appendChild(script);

      return () => {
        if (script.parentNode) {
          script.parentNode.removeChild(script);
        }
      };
    }
  }, [selectedToken, timeframe]);

  const formatNumber = (num: number, decimals: number = 2): string => {
    if (num >= 1e12) return `$${(num / 1e12).toFixed(decimals)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(decimals)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(decimals)}M`;
    if (num >= 1e3) return `$${(num / 1e3).toFixed(decimals)}K`;
    return `$${num.toFixed(decimals)}`;
  };

  const formatPrice = (price: number): string => {
    if (price >= 1000) return price.toFixed(2);
    if (price >= 1) return price.toFixed(4);
    return price.toFixed(6);
  };

  const handleTokenSelect = (symbol: string) => {
    setSelectedToken(symbol);
    setOrderPrice('');
  };

  const handlePlaceOrder = () => {
    // Demo order placement
    alert(`${orderSide.toUpperCase()} ${orderType.toUpperCase()} Order:\n${orderAmount} ${selectedToken} @ ${orderType === 'market' ? 'Market Price' : `$${orderPrice}`}`);
    setOrderAmount('');
  };

  const toggleWatchlist = (symbol: string) => {
    setWatchlist(prev =>
      prev.includes(symbol)
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  return (
    <div className="trading-page">
      <Navbar />

      {/* Market Overview Bar */}
      <div className="market-bar">
        <div className="market-bar-content">
          <div className="market-stats">
            <div className="market-stat">
              <span className="stat-label">Market Cap</span>
              <span className="stat-value">{marketData ? formatNumber(marketData.global_market_cap) : '--'}</span>
            </div>
            <div className="market-stat">
              <span className="stat-label">24h Volume</span>
              <span className="stat-value">{marketData ? formatNumber(marketData.total_volume_24h) : '--'}</span>
            </div>
            <div className="market-stat">
              <span className="stat-label">BTC Dominance</span>
              <span className="stat-value">{marketData ? `${marketData.btc_dominance.toFixed(1)}%` : '--'}</span>
            </div>
          </div>
          <div className="market-ticker">
            {marketData?.tokens.slice(0, 8).map(token => (
              <div
                key={token.symbol}
                className={`ticker-item ${token.price_change_percentage_24h >= 0 ? 'positive' : 'negative'}`}
                onClick={() => handleTokenSelect(token.symbol)}
              >
                <span className="ticker-symbol">{token.symbol}</span>
                <span className="ticker-price">${formatPrice(token.price)}</span>
                <span className="ticker-change">
                  {token.price_change_percentage_24h >= 0 ? '+' : ''}
                  {token.price_change_percentage_24h.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Trading Interface */}
      <div className="trading-container">
        {/* Left Sidebar - Watchlist */}
        <div className="trading-sidebar">
          <div className="sidebar-section">
            <div className="sidebar-header">
              <h3>📊 Watchlist</h3>
              <button className="add-btn">+</button>
            </div>
            <div className="watchlist">
              {marketData?.tokens
                .filter(t => watchlist.includes(t.symbol))
                .map(token => (
                  <div
                    key={token.symbol}
                    className={`watchlist-item ${selectedToken === token.symbol ? 'active' : ''}`}
                    onClick={() => handleTokenSelect(token.symbol)}
                  >
                    <div className="token-info">
                      <span className="token-symbol">{token.symbol}</span>
                      <span className="token-name">{token.name}</span>
                    </div>
                    <div className="token-price-info">
                      <span className="token-price">${formatPrice(token.price)}</span>
                      <span className={`token-change ${token.price_change_percentage_24h >= 0 ? 'positive' : 'negative'}`}>
                        {token.price_change_percentage_24h >= 0 ? '▲' : '▼'}
                        {Math.abs(token.price_change_percentage_24h).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-header">
              <h3>🔥 Markets</h3>
            </div>
            <div className="markets-list">
              {marketData?.tokens.map(token => (
                <div
                  key={token.symbol}
                  className={`market-item ${selectedToken === token.symbol ? 'active' : ''}`}
                  onClick={() => handleTokenSelect(token.symbol)}
                >
                  <div className="market-token">
                    <span className="market-symbol">{token.symbol}</span>
                    <span className="market-pair">/USDT</span>
                  </div>
                  <div className="market-data">
                    <span className="market-price">${formatPrice(token.price)}</span>
                    <span className={`market-change ${token.price_change_percentage_24h >= 0 ? 'positive' : 'negative'}`}>
                      {token.price_change_percentage_24h >= 0 ? '+' : ''}
                      {token.price_change_percentage_24h.toFixed(2)}%
                    </span>
                  </div>
                  <button
                    className={`star-btn ${watchlist.includes(token.symbol) ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleWatchlist(token.symbol);
                    }}
                  >
                    {watchlist.includes(token.symbol) ? '★' : '☆'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="trading-main">
          {/* Token Header */}
          <div className="token-header">
            <div className="token-title">
              <h1>{selectedToken}/USDT</h1>
              <span className="token-full-name">{selectedTokenData?.name}</span>
            </div>
            <div className="token-stats">
              <div className="main-price">
                <span className="current-price">${selectedTokenData ? formatPrice(selectedTokenData.price) : '--'}</span>
                <span className={`price-change ${selectedTokenData && selectedTokenData.price_change_percentage_24h >= 0 ? 'positive' : 'negative'}`}>
                  {selectedTokenData ? (
                    <>
                      {selectedTokenData.price_change_percentage_24h >= 0 ? '+' : ''}
                      ${selectedTokenData.price_change_24h.toFixed(2)}
                      ({selectedTokenData.price_change_percentage_24h.toFixed(2)}%)
                    </>
                  ) : '--'}
                </span>
              </div>
              <div className="token-metrics">
                <div className="metric">
                  <span className="metric-label">24h High</span>
                  <span className="metric-value">${selectedTokenData ? formatPrice(selectedTokenData.high_24h) : '--'}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">24h Low</span>
                  <span className="metric-value">${selectedTokenData ? formatPrice(selectedTokenData.low_24h) : '--'}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">24h Volume</span>
                  <span className="metric-value">{selectedTokenData ? formatNumber(selectedTokenData.volume_24h) : '--'}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Market Cap</span>
                  <span className="metric-value">{selectedTokenData ? formatNumber(selectedTokenData.market_cap) : '--'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Mobile Tab Selector */}
          <div className="mobile-tabs">
            <button
              className={showMobileMenu === 'chart' ? 'active' : ''}
              onClick={() => setShowMobileMenu('chart')}
            >
              Chart
            </button>
            <button
              className={showMobileMenu === 'orderbook' ? 'active' : ''}
              onClick={() => setShowMobileMenu('orderbook')}
            >
              Order Book
            </button>
            <button
              className={showMobileMenu === 'trades' ? 'active' : ''}
              onClick={() => setShowMobileMenu('trades')}
            >
              Trades
            </button>
            <button
              className={showMobileMenu === 'order' ? 'active' : ''}
              onClick={() => setShowMobileMenu('order')}
            >
              Order
            </button>
          </div>

          {/* Chart Section */}
          <div className={`chart-section ${showMobileMenu === 'chart' ? 'mobile-visible' : ''}`}>
            <div className="chart-controls">
              <div className="timeframe-selector">
                {['1h', '4h', '1d', '1w', '1m'].map(tf => (
                  <button
                    key={tf}
                    className={`tf-btn ${timeframe === tf ? 'active' : ''}`}
                    onClick={() => setTimeframe(tf)}
                  >
                    {tf.toUpperCase()}
                  </button>
                ))}
              </div>
              <div className="chart-tools">
                <button className="tool-btn" title="Draw Tools">📐</button>
                <button className="tool-btn" title="Indicators">📈</button>
                <button className="tool-btn" title="Settings">⚙️</button>
                <button className="tool-btn" title="Fullscreen">⛶</button>
              </div>
            </div>
            <div className="chart-container" ref={chartContainerRef}>
              <div id="tradingview-chart" className="tradingview-widget"></div>
            </div>
          </div>

          {/* Bottom Section - Order Book & Trades */}
          <div className="bottom-section">
            {/* Order Book */}
            <div className={`order-book ${showMobileMenu === 'orderbook' ? 'mobile-visible' : ''}`}>
              <div className="section-header">
                <h3>Order Book</h3>
                <div className="book-toggle">
                  <button className="toggle-btn active">Both</button>
                  <button className="toggle-btn">Bids</button>
                  <button className="toggle-btn">Asks</button>
                </div>
              </div>
              <div className="book-header">
                <span>Price (USDT)</span>
                <span>Amount ({selectedToken})</span>
                <span>Total</span>
              </div>
              <div className="book-content">
                <div className="asks">
                  {orderBook.asks.map((ask, i) => (
                    <div key={i} className="book-row ask">
                      <span className="book-price">{formatPrice(ask.price)}</span>
                      <span className="book-amount">{ask.amount.toFixed(4)}</span>
                      <span className="book-total">{ask.total.toFixed(2)}</span>
                      <div className="book-bar" style={{ width: `${(ask.amount / 110) * 100}%` }}></div>
                    </div>
                  ))}
                </div>
                <div className="spread-indicator">
                  <span className="spread-price">${selectedTokenData ? formatPrice(selectedTokenData.price) : '--'}</span>
                  <span className="spread-label">Spread</span>
                </div>
                <div className="bids">
                  {orderBook.bids.map((bid, i) => (
                    <div key={i} className="book-row bid">
                      <span className="book-price">{formatPrice(bid.price)}</span>
                      <span className="book-amount">{bid.amount.toFixed(4)}</span>
                      <span className="book-total">{bid.total.toFixed(2)}</span>
                      <div className="book-bar" style={{ width: `${(bid.amount / 110) * 100}%` }}></div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Recent Trades */}
            <div className={`recent-trades ${showMobileMenu === 'trades' ? 'mobile-visible' : ''}`}>
              <div className="section-header">
                <h3>Recent Trades</h3>
              </div>
              <div className="trades-header">
                <span>Price (USDT)</span>
                <span>Amount ({selectedToken})</span>
                <span>Time</span>
              </div>
              <div className="trades-content">
                {recentTrades.map(trade => (
                  <div key={trade.id} className={`trade-row ${trade.side}`}>
                    <span className="trade-price">{formatPrice(trade.price)}</span>
                    <span className="trade-amount">{trade.amount.toFixed(4)}</span>
                    <span className="trade-time">{trade.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Order Form */}
        <div className={`order-panel ${showMobileMenu === 'order' ? 'mobile-visible' : ''}`}>
          <div className="order-tabs">
            <button
              className={`order-tab ${orderSide === 'buy' ? 'active buy' : ''}`}
              onClick={() => setOrderSide('buy')}
            >
              Buy
            </button>
            <button
              className={`order-tab ${orderSide === 'sell' ? 'active sell' : ''}`}
              onClick={() => setOrderSide('sell')}
            >
              Sell
            </button>
          </div>

          <div className="order-type-selector">
            <button
              className={`type-btn ${orderType === 'limit' ? 'active' : ''}`}
              onClick={() => setOrderType('limit')}
            >
              Limit
            </button>
            <button
              className={`type-btn ${orderType === 'market' ? 'active' : ''}`}
              onClick={() => setOrderType('market')}
            >
              Market
            </button>
          </div>

          <div className="order-form">
            {orderType === 'limit' && (
              <div className="form-group">
                <label>Price</label>
                <div className="input-wrapper">
                  <input
                    type="number"
                    value={orderPrice}
                    onChange={(e) => setOrderPrice(e.target.value)}
                    placeholder="0.00"
                  />
                  <span className="input-suffix">USDT</span>
                </div>
              </div>
            )}

            <div className="form-group">
              <label>Amount</label>
              <div className="input-wrapper">
                <input
                  type="number"
                  value={orderAmount}
                  onChange={(e) => setOrderAmount(e.target.value)}
                  placeholder="0.00"
                />
                <span className="input-suffix">{selectedToken}</span>
              </div>
            </div>

            <div className="amount-shortcuts">
              {['25%', '50%', '75%', '100%'].map(pct => (
                <button key={pct} className="shortcut-btn" onClick={() => setOrderAmount('100')}>
                  {pct}
                </button>
              ))}
            </div>

            <div className="order-summary">
              <div className="summary-row">
                <span>Total</span>
                <span>
                  {orderAmount && orderPrice
                    ? `${(parseFloat(orderAmount) * parseFloat(orderPrice)).toFixed(2)} USDT`
                    : '-- USDT'
                  }
                </span>
              </div>
              <div className="summary-row">
                <span>Fee (0.1%)</span>
                <span>
                  {orderAmount && orderPrice
                    ? `${(parseFloat(orderAmount) * parseFloat(orderPrice) * 0.001).toFixed(4)} USDT`
                    : '-- USDT'
                  }
                </span>
              </div>
            </div>

            <button
              className={`place-order-btn ${orderSide}`}
              onClick={handlePlaceOrder}
              disabled={!orderAmount || (orderType === 'limit' && !orderPrice)}
            >
              {orderSide === 'buy' ? 'Buy' : 'Sell'} {selectedToken}
            </button>
          </div>

          {/* Account Balance */}
          <div className="account-section">
            <div className="section-header">
              <h3>💰 Balances</h3>
            </div>
            <div className="balance-list">
              <div className="balance-item">
                <span className="balance-token">USDT</span>
                <div className="balance-values">
                  <span className="balance-available">10,000.00</span>
                  <span className="balance-label">Available</span>
                </div>
              </div>
              <div className="balance-item">
                <span className="balance-token">{selectedToken}</span>
                <div className="balance-values">
                  <span className="balance-available">0.00</span>
                  <span className="balance-label">Available</span>
                </div>
              </div>
            </div>
          </div>

          {/* Open Orders */}
          <div className="orders-section">
            <div className="section-header">
              <h3>📋 Open Orders</h3>
              <span className="order-count">0</span>
            </div>
            <div className="no-orders">
              <span>No open orders</span>
            </div>
          </div>
        </div>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <span>Loading market data...</span>
        </div>
      )}
    </div>
  );
}
