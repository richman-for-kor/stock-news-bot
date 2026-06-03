"""
종목별 전용 뉴스 수집
- 국내(.KS/.KQ): 네이버 모바일 종목 뉴스 API (JSON)
- 해외: Yahoo Finance 종목 RSS 헤드라인
일반 시황 뉴스로는 개별 종목이 잘 안 잡히므로, 종목 단위로 직접 조회한다.
"""
import requests
import feedparser

HEADERS = {"User-Agent": "Mozilla/5.0"}


def _naver_stock_news(code: str, limit: int = 6) -> list[str]:
    """네이버 모바일 종목 뉴스 (6자리 코드)"""
    url = f"https://m.stock.naver.com/api/news/stock/{code}"
    try:
        r = requests.get(url, params={"pageSize": limit, "page": 1}, headers=HEADERS, timeout=8)
        data = r.json()
        titles = []
        for group in data:
            for it in group.get("items", []):
                t = it.get("titleFull") or it.get("title")
                if t:
                    titles.append(t.strip())
        return titles[:limit]
    except Exception:
        return []


def _yahoo_stock_news(symbol: str, limit: int = 6) -> list[str]:
    """Yahoo Finance 종목 RSS 헤드라인 (해외 종목)"""
    try:
        feed = feedparser.parse(
            f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
        )
        return [e.get("title", "").strip() for e in feed.entries[:limit] if e.get("title")]
    except Exception:
        return []


def fetch_stock_news(symbol: str, name: str, limit: int = 6) -> list[str]:
    """종목 심볼에 맞는 전용 뉴스 헤드라인 리스트 반환"""
    sym = symbol.upper()
    if sym.endswith((".KS", ".KQ")):
        code = sym.split(".")[0]
        return _naver_stock_news(code, limit)
    return _yahoo_stock_news(sym, limit)
