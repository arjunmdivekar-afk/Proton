"""Stock market data provider using yfinance with Indian Rupees (₹) and Global Markets."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import yfinance as yf


# Stock universes categorized into 3 pages of 20 stocks each
STOCK_PAGES: Dict[int, Dict[str, Any]] = {
    1: {
        "title": "Indian Stock Market & NIFTY 50 Leaders (NSE / BSE)",
        "symbols": [
            "^NSEI", "^BSESN", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
            "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "LT.NS", "ITC.NS",
            "KOTAKBANK.NS", "HINDUNILVR.NS", "BAJFINANCE.NS", "MARUTI.NS",
            "SUNPHARMA.NS", "TITAN.NS", "ADANIENT.NS", "WIPRO.NS", "TATASTEEL.NS"
        ],
    },
    2: {
        "title": "Global Tech Giants & AI Leaders",
        "symbols": [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AMD",
            "INTC", "AVGO", "ORCL", "CRM", "NFLX", "ADBE", "CSCO", "QCOM",
            "TXN", "IBM", "NOW", "UBER"
        ],
    },
    3: {
        "title": "Global Indices, Commodities & Crypto",
        "symbols": [
            "^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^N225", "SPY", "QQQ",
            "DIA", "IWM", "VOO", "GLD", "SLV", "USO", "BTC-USD", "ETH-USD",
            "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD"
        ],
    },
}


@dataclass
class StockQuote:
    symbol: str
    name: str = ""
    price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    day_high: float = 0.0
    day_low: float = 0.0
    volume: int = 0
    market_cap: float = 0.0
    currency: str = "INR"
    currency_symbol: str = "₹"
    sparkline_prices: List[float] = field(default_factory=list)


@dataclass
class StockDetail:
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    open_price: float = 0.0
    prev_close: float = 0.0
    day_high: float = 0.0
    day_low: float = 0.0
    fifty_two_high: float = 0.0
    fifty_two_low: float = 0.0
    volume: int = 0
    avg_volume: int = 0
    market_cap: float = 0.0
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    eps: Optional[float] = None
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    target_price: Optional[float] = None
    recommendation: str = "N/A"
    sector: str = "N/A"
    industry: str = "N/A"
    currency: str = "INR"
    currency_symbol: str = "₹"
    history_prices: List[float] = field(default_factory=list)
    history_dates: List[str] = field(default_factory=list)


class StockDataService:
    """Fetches and manages real-time stock quotes and historical charts via yfinance in Rupees (₹)."""

    @staticmethod
    def get_symbols_for_page(page: int = 1) -> List[str]:
        page = max(1, min(len(STOCK_PAGES), page))
        return STOCK_PAGES[page]["symbols"]

    @staticmethod
    def get_page_title(page: int = 1) -> str:
        page = max(1, min(len(STOCK_PAGES), page))
        return STOCK_PAGES[page]["title"]

    @staticmethod
    def get_total_pages() -> int:
        return len(STOCK_PAGES)

    def get_currency_symbol(self, raw_curr: Optional[str] = "INR") -> str:
        """Map currency codes to symbols (defaulting to ₹)."""
        curr = (raw_curr or "INR").upper()
        if curr in ("INR", "RS", "RUPEES", ""):
            return "₹"
        elif curr == "USD":
            return "$"
        elif curr == "EUR":
            return "€"
        elif curr == "GBP":
            return "£"
        return "₹"

    async def fetch_page_quotes(self, page: int = 1) -> List[StockQuote]:
        """Fetch quotes for all 20 stocks on the given page."""
        symbols = self.get_symbols_for_page(page)
        return await self.fetch_quotes(symbols)

    async def fetch_quotes(self, symbols: List[str]) -> List[StockQuote]:
        """Fetch quotes concurrently for a list of ticker symbols."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_quotes_sync, symbols)

    def _fetch_quotes_sync(self, symbols: List[str]) -> List[StockQuote]:
        quotes: List[StockQuote] = []
        try:
            tickers = yf.Tickers(" ".join(symbols))
            for sym in symbols:
                try:
                    t = tickers.tickers.get(sym.upper()) or yf.Ticker(sym)
                    fi = t.fast_info
                    last_p = float(fi.last_price or 0.0)
                    prev_p = float(fi.previous_close or last_p)
                    chg = last_p - prev_p if prev_p else 0.0
                    chg_pct = (chg / prev_p) * 100 if prev_p else 0.0
                    raw_curr = fi.currency or ("INR" if ".NS" in sym or ".BO" in sym or "^NSE" in sym or "^BSE" in sym else "INR")
                    curr_sym = self.get_currency_symbol(raw_curr)

                    quotes.append(
                        StockQuote(
                            symbol=sym,
                            name=self._get_friendly_name(sym),
                            price=last_p,
                            change=chg,
                            change_pct=chg_pct,
                            day_high=float(fi.day_high or last_p),
                            day_low=float(fi.day_low or last_p),
                            volume=int(fi.last_volume or 0),
                            market_cap=float(fi.market_cap or 0.0),
                            currency=raw_curr,
                            currency_symbol=curr_sym,
                        )
                    )
                except Exception:
                    quotes.append(StockQuote(symbol=sym, name=self._get_friendly_name(sym)))
        except Exception:
            for sym in symbols:
                quotes.append(StockQuote(symbol=sym, name=self._get_friendly_name(sym)))
        return quotes

    async def fetch_detail(self, symbol: str, timeframe: str = "1mo") -> Optional[StockDetail]:
        """Fetch comprehensive details and historical chart series for a stock."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_detail_sync, symbol.upper(), timeframe)

    def _fetch_detail_sync(self, symbol: str, timeframe: str = "1mo") -> Optional[StockDetail]:
        try:
            # If user typed an Indian stock symbol without .NS (e.g. RELIANCE, TCS, INFY)
            lookup_sym = symbol
            if lookup_sym in ("RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "SBIN", "LT", "ITC", "TATAMOTORS", "HINDUNILVR", "BAJFINANCE", "MARUTI", "SUNPHARMA", "TITAN", "ADANIENT", "WIPRO", "TATASTEEL"):
                lookup_sym = f"{lookup_sym}.NS"

            t = yf.Ticker(lookup_sym)
            fi = t.fast_info
            info = {}
            try:
                info = t.info or {}
            except Exception:
                pass

            last_p = float(fi.last_price or info.get("currentPrice") or info.get("regularMarketPrice") or 0.0)
            prev_p = float(fi.previous_close or info.get("previousClose") or last_p)
            chg = last_p - prev_p if prev_p else 0.0
            chg_pct = (chg / prev_p) * 100 if prev_p else 0.0

            raw_curr = fi.currency or info.get("currency") or ("INR" if ".NS" in lookup_sym or ".BO" in lookup_sym else "INR")
            curr_sym = self.get_currency_symbol(raw_curr)

            tf_map = {
                "1d": ("1d", "5m"),
                "5d": ("5d", "15m"),
                "1mo": ("1mo", "1d"),
                "6mo": ("6mo", "1d"),
                "1y": ("1y", "1d"),
                "5y": ("5y", "1wk"),
            }
            period, interval = tf_map.get(timeframe.lower(), ("1mo", "1d"))

            hist_prices: List[float] = []
            hist_dates: List[str] = []
            try:
                hist = t.history(period=period, interval=interval)
                if not hist.empty and "Close" in hist:
                    hist_prices = [float(p) for p in hist["Close"].dropna().tolist()]
                    hist_dates = [str(d) for d in hist.index.tolist()]
            except Exception:
                pass

            return StockDetail(
                symbol=lookup_sym,
                name=info.get("shortName") or info.get("longName") or self._get_friendly_name(lookup_sym),
                price=last_p,
                change=chg,
                change_pct=chg_pct,
                open_price=float(fi.open or info.get("open") or 0.0),
                prev_close=prev_p,
                day_high=float(fi.day_high or info.get("dayHigh") or last_p),
                day_low=float(fi.day_low or info.get("dayLow") or last_p),
                fifty_two_high=float(fi.year_high or info.get("fiftyTwoWeekHigh") or 0.0),
                fifty_two_low=float(fi.year_low or info.get("fiftyTwoWeekLow") or 0.0),
                volume=int(fi.last_volume or info.get("volume") or 0),
                avg_volume=int(info.get("averageVolume") or 0),
                market_cap=float(fi.market_cap or info.get("marketCap") or 0.0),
                trailing_pe=info.get("trailingPE"),
                forward_pe=info.get("forwardPE"),
                eps=info.get("trailingEps"),
                beta=info.get("beta"),
                dividend_yield=info.get("dividendYield"),
                target_price=info.get("targetMeanPrice"),
                recommendation=info.get("recommendationKey", "N/A").upper(),
                sector=info.get("sector", "N/A"),
                industry=info.get("industry", "N/A"),
                currency=raw_curr,
                currency_symbol=curr_sym,
                history_prices=hist_prices,
                history_dates=hist_dates,
            )
        except Exception:
            return None

    def _get_friendly_name(self, sym: str) -> str:
        names = {
            # Indian Indices & NSE Stocks
            "^NSEI": "NIFTY 50 Index", "^BSESN": "SENSEX 30 Index",
            "RELIANCE.NS": "Reliance Industries", "TCS.NS": "Tata Consultancy Services",
            "HDFCBANK.NS": "HDFC Bank Ltd", "INFY.NS": "Infosys Ltd",
            "ICICIBANK.NS": "ICICI Bank Ltd", "BHARTIARTL.NS": "Bharti Airtel Ltd",
            "SBIN.NS": "State Bank of India", "LT.NS": "Larsen & Toubro Ltd",
            "ITC.NS": "ITC Limited", "TATAMOTORS.NS": "Tata Motors Ltd",
            "HINDUNILVR.NS": "Hindustan Unilever", "BAJFINANCE.NS": "Bajaj Finance Ltd",
            "MARUTI.NS": "Maruti Suzuki Ltd", "SUNPHARMA.NS": "Sun Pharma Industries",
            "TITAN.NS": "Titan Company Ltd", "ADANIENT.NS": "Adani Enterprises",
            "WIPRO.NS": "Wipro Limited", "TATASTEEL.NS": "Tata Steel Ltd",
            # US Tech Leaders
            "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "NVDA": "NVIDIA Corp.",
            "GOOGL": "Alphabet Inc.", "AMZN": "Amazon.com Inc.", "META": "Meta Platforms",
            "TSLA": "Tesla Inc.", "AMD": "Advanced Micro Devices", "INTC": "Intel Corp.",
            "AVGO": "Broadcom Inc.", "ORCL": "Oracle Corp.", "CRM": "Salesforce Inc.",
            "NFLX": "Netflix Inc.", "ADBE": "Adobe Inc.", "CSCO": "Cisco Systems",
            "QCOM": "Qualcomm Inc.", "TXN": "Texas Instruments", "IBM": "IBM Corp.",
            "NOW": "ServiceNow Inc.", "UBER": "Uber Technologies",
            # Global Indices & Crypto
            "^GSPC": "S&P 500 Index", "^DJI": "Dow Jones Industrial", "^IXIC": "Nasdaq Composite",
            "^RUT": "Russell 2000", "^FTSE": "FTSE 100", "^N225": "Nikkei 225",
            "SPY": "SPDR S&P 500 ETF", "QQQ": "Invesco QQQ ETF", "DIA": "SPDR Dow Jones ETF",
            "IWM": "iShares Russell 2000", "VOO": "Vanguard S&P 500", "GLD": "SPDR Gold Shares",
            "SLV": "iShares Silver Trust", "USO": "United States Oil Fund",
            "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
            "BNB-USD": "Binance Coin", "XRP-USD": "Ripple", "DOGE-USD": "Dogecoin",
        }
        return names.get(sym, sym)
