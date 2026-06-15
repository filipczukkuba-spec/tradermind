import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


SECTORS = {
    "XLK": "Technology", "XLF": "Financials", "XLE": "Energy",
    "XLV": "Healthcare", "XLU": "Utilities", "XLI": "Industrials",
    "XLY": "Consumer Discretionary", "XLP": "Consumer Staples",
    "XLB": "Materials", "XLRE": "Real Estate", "XLC": "Communication",
}

MACRO_TICKERS = {
    "SPY": "S&P 500", "QQQ": "Nasdaq 100", "IWM": "Russell 2000",
    "EFA": "Intl Developed", "EEM": "Emerging Markets",
    "GLD": "Gold", "USO": "Oil", "UUP": "US Dollar",
    "TLT": "20Y Treasury", "IEF": "7-10Y Treasury",
    "HYG": "High Yield Bonds", "LQD": "Investment Grade Bonds",
    "^VIX": "VIX", "^TNX": "10Y Yield", "^IRX": "3M Yield",
}

STOCK_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B",
    "JPM", "V", "UNH", "XOM", "LLY", "AVGO", "JNJ", "MA", "PG",
    "HD", "MRK", "CVX", "ABBV", "COST", "ADBE", "WMT", "CRM",
    "BAC", "NFLX", "ACN", "TMO", "AMD", "ORCL", "CSCO", "PFE",
    "DHR", "ABT", "MCD", "NEE", "TXN", "AMGN", "PM", "RTX",
    "HON", "IBM", "GS", "SPGI", "LOW", "CAT", "NOW", "ISRG",
    "PANW", "SNPS", "CDNS", "MSTR", "COIN", "PLTR", "APP", "HOOD",
]


def _safe_float(v) -> float | None:
    try:
        f = float(v)
        return None if np.isnan(f) or np.isinf(f) else round(f, 4)
    except Exception:
        return None


def _momentum(closes: pd.Series, days: int) -> float | None:
    if len(closes) < days + 1:
        return None
    return _safe_float((closes.iloc[-1] / closes.iloc[-days] - 1) * 100)


def _rsi(closes: pd.Series, period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    delta = closes.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return _safe_float(rsi.iloc[-1])


def _macd_signal(closes: pd.Series) -> str | None:
    if len(closes) < 35:
        return None
    ema12 = closes.ewm(span=12, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    h, h_prev = float(hist.iloc[-1]), float(hist.iloc[-2])
    if h > 0 and h > h_prev:
        return "bullish_accelerating"
    elif h > 0:
        return "bullish"
    elif h < 0 and h < h_prev:
        return "bearish_accelerating"
    else:
        return "bearish"


def _bb_position(closes: pd.Series, period: int = 20) -> float | None:
    if len(closes) < period:
        return None
    sma = closes.rolling(period).mean()
    std = closes.rolling(period).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    rng = float(upper.iloc[-1]) - float(lower.iloc[-1])
    if rng == 0:
        return 0.5
    return _safe_float((float(closes.iloc[-1]) - float(lower.iloc[-1])) / rng)


def _volume_ratio(volumes: pd.Series) -> float | None:
    if len(volumes) < 21:
        return None
    avg = float(volumes.iloc[-21:-1].mean())
    if avg == 0:
        return None
    return _safe_float(float(volumes.iloc[-1]) / avg)


def _fetch_closes(symbol: str, days: int = 300) -> tuple[pd.Series | None, pd.Series | None]:
    try:
        end = datetime.today()
        start = end - timedelta(days=days + 60)
        df = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)
        if df.empty or len(df) < 20:
            return None, None
        closes = df["Close"].squeeze()
        volumes = df["Volume"].squeeze() if "Volume" in df.columns else None
        return closes, volumes
    except Exception:
        return None, None


def _enrich(symbol: str, closes: pd.Series, volumes: pd.Series | None, name: str = "") -> dict:
    price = _safe_float(closes.iloc[-1])
    high_52w = _safe_float(closes.tail(252).max())
    low_52w = _safe_float(closes.tail(252).min())
    pct_from_high = _safe_float((price / high_52w - 1) * 100) if high_52w else None

    return {
        "symbol": symbol,
        "name": name or symbol,
        "price": price,
        "mom_1m": _momentum(closes, 21),
        "mom_3m": _momentum(closes, 63),
        "mom_6m": _momentum(closes, 126),
        "mom_12m": _momentum(closes, 252),
        "rsi_14": _rsi(closes),
        "macd": _macd_signal(closes),
        "bb_position": _bb_position(closes),  # 0=oversold, 1=overbought
        "volume_ratio": _volume_ratio(volumes) if volumes is not None else None,
        "52w_high": high_52w,
        "52w_low": low_52w,
        "pct_from_52w_high": pct_from_high,
    }


def _score(d: dict) -> float:
    score = 0
    if d.get("mom_1m"): score += d["mom_1m"] * 0.15
    if d.get("mom_3m"): score += d["mom_3m"] * 0.35
    if d.get("mom_6m"): score += d["mom_6m"] * 0.30
    if d.get("mom_12m"): score += d["mom_12m"] * 0.20
    rsi = d.get("rsi_14")
    if rsi:
        if 50 < rsi < 70:
            score += 5
        elif rsi >= 70:
            score -= 3
        elif rsi < 35:
            score -= 8
    macd = d.get("macd", "")
    if macd == "bullish_accelerating": score += 8
    elif macd == "bullish": score += 4
    elif macd == "bearish_accelerating": score -= 8
    elif macd == "bearish": score -= 4
    vol = d.get("volume_ratio")
    if vol and vol > 1.5 and (d.get("mom_1m") or 0) > 0:
        score += 5
    return round(score, 2)


def fetch_all_market_data() -> dict:
    print("Fetching macro data...")
    macro = {}
    for sym, name in MACRO_TICKERS.items():
        closes, vols = _fetch_closes(sym)
        if closes is not None:
            macro[sym] = _enrich(sym, closes, vols, name)

    vix_val = macro.get("^VIX", {}).get("price")
    y10 = macro.get("^TNX", {}).get("price")
    y3m = macro.get("^IRX", {}).get("price")
    yield_spread = _safe_float(y10 - y3m) if y10 and y3m else None
    hyg_mom = macro.get("HYG", {}).get("mom_3m")
    spy_mom3 = macro.get("SPY", {}).get("mom_3m")

    if vix_val:
        if vix_val < 15: vix_regime = "extreme_complacency"
        elif vix_val < 20: vix_regime = "low_fear"
        elif vix_val < 30: vix_regime = "elevated_fear"
        else: vix_regime = "high_fear_panic"
    else:
        vix_regime = "unknown"

    if yield_spread is not None:
        curve_regime = "inverted" if yield_spread < 0 else ("flat" if yield_spread < 0.5 else "normal")
    else:
        curve_regime = "unknown"

    macro_context = {
        "vix": vix_val,
        "vix_regime": vix_regime,
        "10y_yield": y10,
        "3m_yield": y3m,
        "yield_curve_spread_10y_minus_3m": yield_spread,
        "yield_curve_regime": curve_regime,
        "credit_stress": "elevated" if (hyg_mom or 0) < -3 else "normal",
        "market_trend": "bullish" if (spy_mom3 or 0) > 3 else ("bearish" if (spy_mom3 or 0) < -3 else "neutral"),
        "key_assets": {k: v for k, v in macro.items() if k not in ("^VIX", "^TNX", "^IRX")},
    }

    print("Fetching sector data...")
    sectors = []
    spy_mom3 = macro.get("SPY", {}).get("mom_3m") or 0
    for sym, name in SECTORS.items():
        closes, vols = _fetch_closes(sym)
        if closes is not None:
            d = _enrich(sym, closes, vols, name)
            d["vs_spy_3m"] = _safe_float((d.get("mom_3m") or 0) - spy_mom3)
            d["score"] = _score(d)
            sectors.append(d)
    sectors.sort(key=lambda x: x.get("score", 0), reverse=True)

    print("Fetching stock universe...")
    stocks = []
    for sym in STOCK_UNIVERSE:
        closes, vols = _fetch_closes(sym)
        if closes is None:
            continue
        try:
            info = yf.Ticker(sym).info
            name = info.get("longName") or info.get("shortName", sym)
            pe = _safe_float(info.get("trailingPE"))
            fpe = _safe_float(info.get("forwardPE"))
            mcap = _safe_float((info.get("marketCap") or 0) / 1e9)
            sector = info.get("sector", "")
        except Exception:
            name, pe, fpe, mcap, sector = sym, None, None, None, ""

        d = _enrich(sym, closes, vols, name)
        d.update({"sector": sector, "pe_trailing": pe, "pe_forward": fpe, "market_cap_b": mcap})
        d["score"] = _score(d)
        stocks.append(d)

    stocks.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_momentum = stocks[:20]
    oversold_quality = [
        s for s in stocks
        if (s.get("rsi_14") or 100) < 38
        and (s.get("mom_6m") or -99) > -15
        and (s.get("market_cap_b") or 0) > 50
    ][:8]

    return {
        "date": datetime.today().strftime("%Y-%m-%d"),
        "macro_context": macro_context,
        "sector_rotation": sectors,
        "top_momentum_stocks": top_momentum,
        "oversold_quality_watchlist": oversold_quality,
        "full_stock_scores": [{"symbol": s["symbol"], "score": s["score"], "mom_3m": s.get("mom_3m")} for s in stocks],
    }
