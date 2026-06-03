"""
거시경제 핵심 지표 수집 — yfinance 대신 무료 API 사용 (Termux 호환)
"""
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

ALERT_THRESHOLDS = {
    "TNX":  {"name": "미국 10년물 국채금리", "unit": "%",  "alert_above": 4.5,  "emoji": "🇺🇸📈"},
    "BRENT":{"name": "브렌트유",              "unit": "$",  "alert_above": 100,  "emoji": "🛢️"},
    "VIX":  {"name": "공포지수(VIX)",         "unit": "",   "alert_above": 40,   "emoji": "😱"},
    "KRW":  {"name": "원/달러 환율",           "unit": "원", "alert_above": 1450, "emoji": "💱"},
}


def is_korean_stock(ticker: str) -> bool:
    return ticker.upper().endswith((".KS", ".KQ"))


def format_price(ticker: str, price: float | None) -> str:
    """티커에 따라 원화/달러 포맷 자동 적용"""
    if price is None:
        return "N/A"
    if is_korean_stock(ticker):
        return f"{int(price):,}원"
    return f"${price:,.2f}"


def format_change(change_pct: float | None) -> str:
    """등락률을 화살표와 함께 포맷 (▲상승 ▼하락)"""
    if change_pct is None:
        return ""
    if change_pct > 0:
        return f"🔺{change_pct:+.2f}%"
    if change_pct < 0:
        return f"🔻{change_pct:.2f}%"
    return f"⏸{change_pct:.2f}%"


def _yahoo_quote(symbol: str) -> dict:
    """현재가 + 전일 대비 등락률을 한 번의 호출로 조회

    range=1d 기준으로 meta의 전일 종가 필드를 우선 사용해 '일일' 등락률을 계산한다.
    (range를 늘리면 chartPreviousClose가 며칠 전 종가가 되어 등락률이 왜곡됨)
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        r = requests.get(url, headers=HEADERS, timeout=8)
        meta = r.json()["chart"]["result"][0]["meta"]
        price = meta["regularMarketPrice"]
        # 전일 종가: regularMarketPreviousClose → previousClose → chartPreviousClose 순
        prev = (meta.get("regularMarketPreviousClose")
                or meta.get("previousClose")
                or meta.get("chartPreviousClose"))
        change_pct = round((price - prev) / prev * 100, 2) if prev else None
        return {"price": round(price, 2), "change_pct": change_pct}
    except Exception:
        return {"price": None, "change_pct": None}


def _yahoo_price(symbol: str) -> float | None:
    """Yahoo Finance 비공식 API (pandas 불필요)"""
    return _yahoo_quote(symbol)["price"]


def get_all_indicators() -> dict:
    symbols = {
        "TNX":      ("^TNX",      "미국 10년물 국채금리"),
        "TYX":      ("^TYX",      "미국 30년물 국채금리"),
        "VIX":      ("^VIX",      "공포지수 VIX"),
        "BRENT":    ("BZ=F",      "브렌트유"),
        "GOLD":     ("GC=F",      "금(Gold)"),
        "DXY":      ("DX-Y.NYB",  "달러 인덱스(DXY)"),
        "KRW":      ("USDKRW=X",  "원/달러 환율"),
        "SP500":    ("^GSPC",     "S&P 500"),
        "NASDAQ":   ("^IXIC",     "NASDAQ"),
        "KOSPI":    ("^KS11",     "KOSPI"),
    }
    result = {}
    for key, (symbol, name) in symbols.items():
        quote = _yahoo_quote(symbol)
        price = quote["price"]
        threshold = ALERT_THRESHOLDS.get(key)
        is_alert = bool(threshold and price and price >= threshold["alert_above"])
        result[key] = {
            "name": name, "price": price, "change_pct": quote["change_pct"],
            "is_alert": is_alert, "threshold": threshold,
        }
    return result


def get_bigtech_prices() -> dict:
    tickers = {
        "NVDA": "엔비디아", "MSFT": "마이크로소프트", "AMZN": "아마존",
        "META": "메타", "GOOGL": "구글", "AMD": "AMD", "INTC": "인텔",
        "005930.KS": "삼성전자", "000660.KS": "SK하이닉스",
    }
    result = {}
    for ticker, name in tickers.items():
        result[ticker] = {"name": name, "price": _yahoo_price(ticker)}
    return result


def check_red_alerts() -> list[dict]:
    alerts = []
    for key, info in ALERT_THRESHOLDS.items():
        symbol_map = {"TNX": "^TNX", "BRENT": "BZ=F", "VIX": "^VIX", "KRW": "USDKRW=X"}
        price = _yahoo_price(symbol_map[key])
        if price and price >= info["alert_above"]:
            alerts.append({
                "name": info["name"], "price": price,
                "threshold": info["alert_above"], "unit": info["unit"], "emoji": info["emoji"],
            })
    return alerts
