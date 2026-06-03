import re
import html
import feedparser
from config import RSS_FEEDS, BREAKING_KEYWORDS
from db.users import is_news_sent, mark_news_sent
from news.translator import translate_items


def clean_html(text: str) -> str:
    """RSS 본문에 섞인 HTML 태그·엔티티 제거 후 공백 정리"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)   # 태그 제거
    text = html.unescape(text)              # &amp; &nbsp; 등 복원
    return re.sub(r"\s+", " ", text).strip()


def is_breaking(title: str) -> bool:
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in BREAKING_KEYWORDS)


def fetch_feed(url: str) -> list[dict]:
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:10]:
            items.append({
                "title": clean_html(entry.get("title", "")),
                "link": entry.get("link", ""),
                "summary": clean_html(entry.get("summary", ""))[:200],
                "published": entry.get("published", ""),
                "source": feed.feed.get("title", url),
            })
        return items
    except Exception:
        return []


def collect_all_news(translate: bool = True, only_new: bool = True) -> dict[str, list[dict]]:
    """모든 RSS 피드에서 뉴스 수집 후 카테고리별 반환

    translate=False: 번역 생략 (속보 사전 필터링 등 대량 호출 시)
    only_new=False:  발송 여부와 무관하게 전체 반환 (분석용 — 이미 발송된 뉴스도 매칭에 사용)
    """
    result = {}
    for category, urls in RSS_FEEDS.items():
        items = []
        for url in urls:
            items.extend(fetch_feed(url))
        if only_new:
            items = [item for item in items if not is_news_sent(item["link"])]
        result[category] = translate_items(items) if translate else items
    return result


def collect_breaking_news() -> list[dict]:
    """속보 키워드 포함된 미발송 뉴스만 추출 — 매칭된 건만 번역하여 부하 절감"""
    from news.translator import translate_item
    all_news = collect_all_news(translate=False)  # 사전 필터링은 원문으로
    breaking = []
    for category, items in all_news.items():
        for item in items:
            # 원문 제목으로 속보 판정 (키워드에 한/영 모두 포함)
            if is_breaking(item["title"]):
                translated = translate_item(item)
                translated["category"] = category
                breaking.append(translated)
    return breaking
