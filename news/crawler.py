"""
주요 뉴스 크롤러 — 네이버 금융, 연합뉴스, 인베스팅닷컴
"""
import re
import aiohttp
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


async def fetch(url: str, session: aiohttp.ClientSession) -> str:
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=8)) as r:
            return await r.text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


async def crawl_naver_finance_news() -> list[dict]:
    """네이버 금융 뉴스 크롤링"""
    url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
    async with aiohttp.ClientSession() as session:
        html = await fetch(url, session)
    soup = BeautifulSoup(html, "lxml")
    items = []
    for a in soup.select("dl.articleSubject a")[:10]:
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if href and not href.startswith("http"):
            href = "https://finance.naver.com" + href
        if title:
            items.append({"title": title, "link": href, "source": "네이버금융", "summary": ""})
    return items


async def crawl_yonhap_economy() -> list[dict]:
    """연합뉴스 경제 RSS"""
    import feedparser
    from news.collector import clean_html
    feed = feedparser.parse("https://www.yna.co.kr/rss/economy.xml")
    items = []
    for entry in feed.entries[:10]:
        items.append({
            "title": clean_html(entry.get("title", "")),
            "link": entry.get("link", ""),
            "source": "연합뉴스",
            "summary": clean_html(entry.get("summary", ""))[:150],
        })
    return items


async def crawl_investing_news() -> list[dict]:
    """인베스팅닷컴 한국 뉴스"""
    url = "https://kr.investing.com/news/stock-market-news"
    async with aiohttp.ClientSession() as session:
        html = await fetch(url, session)
    soup = BeautifulSoup(html, "lxml")
    items = []
    for article in soup.select("article.js-article-item")[:8]:
        a = article.select_one("a.title")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if href and not href.startswith("http"):
            href = "https://kr.investing.com" + href
        items.append({"title": title, "link": href, "source": "인베스팅닷컴", "summary": ""})
    return items


async def crawl_all_news(translate: bool = True) -> list[dict]:
    """모든 크롤링 소스 병렬 수집 (translate=False면 번역 생략)"""
    import asyncio
    from news.translator import translate_items
    results = await asyncio.gather(
        crawl_naver_finance_news(),
        crawl_yonhap_economy(),
        crawl_investing_news(),
        return_exceptions=True,
    )
    items = []
    for r in results:
        if isinstance(r, list):
            items.extend(r)
    if not translate:
        return items
    # 번역은 블로킹이므로 스레드에서 실행
    return await asyncio.to_thread(translate_items, items)
