"""
종목 분석 — 규칙 기반 + Claude AI 병행
AI 사용 불가 시 규칙 기반으로 자동 폴백
블로킹 호출(네트워크/AI)은 asyncio.to_thread로 이벤트 루프를 막지 않는다.
"""
import asyncio
from market.indicators import _yahoo_price, format_price
from market.rule_analyst import analyze_rule_based, _find_related_news_from_list
from market.ai_client import ai_generate
from db.users import get_watchlist
from news.collector import collect_all_news
from news.crawler import crawl_all_news


def _collect_all_news_flat() -> list[dict]:
    # 분석용: 이미 발송된 뉴스도 포함해 매칭 폭을 넓힘
    rss = collect_all_news(only_new=False)
    return [item for items in rss.values() for item in items]


def analyze_stock_ai(ticker: str, name: str, price: float | None, related_news: list[str]) -> str:
    """AI 분석 — 실패 시 예외 발생 (호출부에서 규칙 기반 폴백)"""
    news_text = "\n".join(related_news) if related_news else "관련 뉴스 없음"
    price_text = format_price(ticker, price) if price else "조회 불가"

    prompt = f"""당신은 주식 분석 전문가입니다. 아래 정보를 바탕으로 종목을 간결하게 분석해주세요.

종목: {name} ({ticker})
현재가: {price_text}

관련 최신 뉴스:
{news_text}

다음 형식으로 반드시 답변하세요 (각 항목 1줄):
📊 시황: [현재 상황 요약]
🔍 분석: [핵심 판단 근거]
💡 신호: [매수 / 매도 / 관망 / 호재 / 위험 / 급락주의] 중 하나
⚠️ 주의: [리스크 또는 주목할 점]

반드시 한국어로 답변하세요."""

    return ai_generate(prompt, max_tokens=600)


def analyze_stock(ticker: str, name: str, price: float | None, related_news: list[str]) -> str:
    """AI + 규칙 기반 병행 분석 (동기 — 호출부에서 to_thread로 감쌀 것)"""
    rule_result = analyze_rule_based(ticker, name, related_news)
    try:
        ai_result = analyze_stock_ai(ticker, name, price, related_news)
        return f"{rule_result}\n\n🤖 <b>AI 분석</b>\n{ai_result}"
    except Exception as e:
        if "RATE_LIMIT" in str(e) or "429" in str(e):
            note = "⏳ AI 일시 혼잡(무료 분당 한도) — 잠시 후 다시 시도하세요"
        else:
            note = "ℹ️ AI 분석 일시 불가 — 규칙 기반만 표시"
        return f"{rule_result}\n\n<i>{note}</i>"


def _analyze_one(item: dict, all_news: list[dict]) -> str:
    """종목 1개 분석 (블로킹) — to_thread용"""
    from news.stock_news import fetch_stock_news
    ticker, name = item["ticker"], item["name"]
    price = _yahoo_price(ticker)
    # 종목 전용 뉴스 + 일반 시황 뉴스 매칭 결과 결합
    stock_news = [f"- {t}" for t in fetch_stock_news(ticker, name)]
    related = _find_related_news_from_list(ticker, name, all_news)
    combined = stock_news + [r for r in related if r not in stock_news]
    body = analyze_stock(ticker, name, price, combined[:10])
    return f"━━━━━━━━━━━━━━\n{body}"


async def analyze_items(items: list[dict], header: str = "⭐ <b>관심 종목 분석</b>") -> str:
    """주어진 종목 리스트 분석 (저장 여부 무관). items: [{ticker, name}, ...]"""
    if not items:
        return ""

    # 뉴스 수집 (블로킹 → 스레드)
    all_news = await asyncio.to_thread(_collect_all_news_flat)
    try:
        crawled = await crawl_all_news()
        all_news.extend(crawled)
    except Exception:
        pass

    # 종목별 분석 — 동시 2개로 제한 (무료 분당 한도 초과 방지)
    sem = asyncio.Semaphore(2)

    async def _one(it):
        async with sem:
            return await asyncio.to_thread(_analyze_one, it, all_news)

    results = await asyncio.gather(*[_one(it) for it in items])
    return f"{header}\n\n" + "\n".join(results)


async def analyze_watchlist() -> str:
    """저장된 관심 종목 전체 분석 — 브리핑용"""
    return await analyze_items(get_watchlist())
