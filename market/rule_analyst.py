"""
규칙 기반 종목 분석 — AI 없이도 동작하는 폴백 분석기
가격 변동률 + 뉴스 키워드 감성 분석으로 신호 생성
"""
from market.indicators import _yahoo_price, format_price

# 호재 키워드
BULLISH_KEYWORDS = [
    "급등", "상승", "호재", "수주", "잭팟", "흑자", "흑자전환", "매출 증가", "신고가",
    "목표가 상향", "수익", "성장", "투자 확대", "계약", "파트너십", "신제품", "승인",
    "사상 최대", "최대 실적", "신기록", "호실적", "어닝 서프라이즈", "강세", "돌파",
    "수혜", "모멘텀", "반등", "훈풍", "순항", "기대", "확대", "증가", "주도", "급증",
    "surges", "rises", "jumps", "soars", "beats", "record", "growth", "upgrade",
    "buy", "bullish", "strong", "positive", "profit", "rally", "gains",
]

# 악재 키워드
BEARISH_KEYWORDS = [
    "급락", "하락", "악재", "적자", "적자전환", "손실", "목표가 하향", "매도", "위험",
    "소송", "조사", "리콜", "파산", "실적 쇼크", "어닝 쇼크", "구조조정", "감원",
    "급감", "부진", "우려", "경계", "약세", "하향", "충격", "위기", "둔화", "감소",
    "drops", "falls", "plunges", "tumbles", "misses", "lawsuit", "investigation",
    "recall", "bearish", "weak", "negative", "loss", "cut", "downgrade", "sell",
]

# 위험 키워드
DANGER_KEYWORDS = [
    "전쟁", "제재", "금지", "파산", "상장폐지", "분식회계", "횡령", "압수수색",
    "디폴트", "거래정지", "감자", "배임",
    "war", "sanction", "ban", "bankruptcy", "fraud", "delisting", "default",
]


def _find_related_news_from_list(ticker: str, name: str, all_news: list[dict]) -> list[str]:
    """수집된 뉴스에서 해당 종목 관련 기사 추출"""
    keywords = [ticker.upper(), name, ticker.split(".")[0].upper()]
    related = []
    for item in all_news:
        text = item.get("title", "") + " " + item.get("summary", "")
        if any(kw.lower() in text.lower() for kw in keywords):
            related.append(f"- {item.get('title', '')}")
    return related[:8]


def _score_news(related_news: list[str]) -> tuple[int, int, int]:
    """뉴스에서 호재/악재/위험 점수 계산"""
    bull, bear, danger = 0, 0, 0
    text = " ".join(related_news).lower()
    for kw in BULLISH_KEYWORDS:
        if kw.lower() in text:
            bull += 1
    for kw in BEARISH_KEYWORDS:
        if kw.lower() in text:
            bear += 1
    for kw in DANGER_KEYWORDS:
        if kw.lower() in text:
            danger += 1
    return bull, bear, danger


def _get_price_change(ticker: str) -> float | None:
    """전일 대비 등락률 계산"""
    try:
        import requests
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        data = r.json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        if len(closes) >= 2:
            return round((closes[-1] - closes[-2]) / closes[-2] * 100, 2)
    except Exception:
        pass
    return None


def analyze_rule_based(ticker: str, name: str, related_news: list[str]) -> str:
    """규칙 기반 분석 결과 반환"""
    price = _yahoo_price(ticker)
    change = _get_price_change(ticker)
    bull, bear, danger = _score_news(related_news)

    # 신호 결정
    if danger > 0:
        signal = "🚨 위험"
    elif change is not None and change <= -5:
        signal = "📉 급락 주의"
    elif change is not None and change >= 5:
        signal = "📈 급등 (과열 주의)"
    elif bull > bear + 1:
        signal = "✅ 호재"
    elif bear > bull + 1:
        signal = "❌ 악재"
    elif change is not None and change > 1:
        signal = "🟡 단기 상승"
    elif change is not None and change < -1:
        signal = "🟠 단기 하락"
    else:
        signal = "⏸ 관망"

    price_text = format_price(ticker, price)
    change_text = f"{change:+.2f}%" if change is not None else "N/A"

    lines = [
        f"📌 <b>[규칙분석] {name} ({ticker})</b>",
        f"💰 현재가: <code>{price_text}</code> | 등락: <code>{change_text}</code>",
        f"📰 뉴스: 호재 {bull}건 / 악재 {bear}건 / 위험 {danger}건",
        f"💡 신호: {signal}",
    ]
    return "\n".join(lines)
