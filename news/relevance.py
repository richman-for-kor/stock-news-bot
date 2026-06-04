"""
증시 관련성 필터 — 뉴스 요약에 '시장에 영향 주는' 헤드라인만 통과시킨다.
키워드 방식(무료·빠름)이라 매시간/매5분 돌려도 부담 없음.

튜닝 포인트: 아래 세 목록만 손보면 민감도가 바뀝니다.
- MARKET_KEYWORDS : 이게 하나도 없으면 '증시와 무관'으로 보고 버림
- STRONG_MARKET   : 강한 증시 신호 (노이즈와 같이 있어도 살림, 예: '게임주 급등')
- NOISE_KEYWORDS  : 명백한 비증시(연예·스포츠·날씨 등) → 강한 신호 없으면 버림
"""

# 강한 증시 신호 — 이게 있으면 노이즈 단어가 섞여도 통과
STRONG_MARKET = [
    "코스피", "코스닥", "나스닥", "다우", "s&p", "증시", "지수", "선물",
    "주가", "상한가", "하한가", "급등", "급락", "폭등", "폭락", "신고가", "신저가",
    "최고치", "최저치", "매수", "매도", "순매수", "순매도", "외국인", "기관",
    "시가총액", "시총", "실적", "영업이익", "순이익", "어닝", "수주", "공시",
    "상장", "ipo", "금리", "환율", "fomc", "연준", "fed", "국채", "유가",
    "earnings", "stocks", "shares", "nasdaq", "rally", "surge", "plunge",
    "rate cut", "rate hike", "merger", "settle lower", "settle higher",
]

# 일반 증시 관련 키워드 (섹터·종목·매크로 포함) — 최소 1개는 있어야 통과
MARKET_KEYWORDS = STRONG_MARKET + [
    "주식", "증권", "투자", "배당", "자사주", "공모", "인수", "합병", "지분",
    "거래량", "밸류", "목표가", "리포트", "전망", "물가", "인플레", "cpi", "ppi",
    "기준금리", "긴축", "완화", "수출", "무역", "관세", "파산", "입찰",
    "반도체", "hbm", "2차전지", "배터리", "바이오", "제약", "자동차",
    "조선", "방산", "원전", "로봇", "전력", "신재생", "리츠",
    "삼성전자", "sk하이닉스", "하이닉스", "현대차", "포스코", "한화",
    "엔비디아", "테슬라", "애플", "마이크로소프트", "구글", "아마존", "메타", "tsmc",
    "비트코인", "이더리움", "리플", "xrp", "도지", "솔라나", "알트코인",
    "코인", "가상자산", "암호화폐", "crypto", "bitcoin", "token",
    "gold", "silver", "crude", "oil prices",
    "market", "equity", "revenue", "dividend", "yield", "treasury", "inflation", "fed",
]

# 비증시 노이즈 — 강한 증시 신호가 없으면 버림
NOISE_KEYWORDS = [
    "연예", "배우", "가수", "아이돌", "드라마", "영화", "예능", "뮤직", "콘서트",
    "스포츠", "축구", "야구", "농구", "골프", "올림픽", "월드컵", "리그",
    "날씨", "기온", "미세먼지", "태풍", "장마", "폭염", "한파",
    "운세", "별자리", "로또", "복권",
    "부고", "인사동정", "포토", "화보", "갤러리", "movie", "celebrity", "sports",
    "카드 혜택", "할인", "쿠폰", "적립", "이벤트 안내", "사은품", "경품",
    "분양", "청약", "매물", "전세", "월세",
    "맛집", "레시피", "여행", "관광", "건강 팁", "다이어트",
]


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


def is_market_relevant(item: dict) -> bool:
    """이 뉴스가 증시에 의미 있는지 판단"""
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    if not text.strip():
        return False
    # 명백한 노이즈는 강한 신호가 함께 있지 않으면 제외
    if _has_any(text, NOISE_KEYWORDS) and not _has_any(text, STRONG_MARKET):
        return False
    # 증시 관련 키워드가 최소 하나는 있어야 통과
    return _has_any(text, MARKET_KEYWORDS)


def filter_relevant(items: list[dict]) -> list[dict]:
    return [it for it in items if is_market_relevant(it)]


# ── AI 기반 관련성 필터 (배치 1회 호출) ─────────────
def filter_relevant_ai(items: list[dict]) -> list[dict]:
    """Gemini가 헤드라인 의미로 증시 관련만 선별. 실패 시 키워드 폴백."""
    if not items:
        return []
    import re
    from market.ai_client import ai_available, ai_generate

    if not ai_available():
        return filter_relevant(items)

    numbered = "\n".join(f"{i+1}. {it.get('title','')}" for i, it in enumerate(items))
    prompt = (
        "아래는 뉴스 헤드라인 목록입니다. 이 중 '주식·증시·시장에 실제로 "
        "영향을 주거나 시장/종목/거시경제 동향을 다루는' 뉴스의 번호만 고르세요.\n"
        "제외 대상: 정치 가십, 사건사고, 연예·스포츠·날씨, 단순 행사/홍보/채용, "
        "인물 일상, 노조·내부 이슈 등 시장과 직접 무관한 것.\n\n"
        f"{numbered}\n\n"
        "관련 있는 번호만 쉼표로 답하세요. 예) 1, 4, 7"
    )
    try:
        resp = ai_generate(prompt, max_tokens=300)
        nums = re.findall(r"\d+", resp)
        if not nums:                       # 파싱 실패 → 키워드 폴백
            return filter_relevant(items)
        keep = {int(n) for n in nums}
        return [items[i - 1] for i in sorted(keep) if 1 <= i <= len(items)]
    except Exception:
        return filter_relevant(items)      # AI 오류 → 키워드 폴백


def filter_news_by_category_ai(news_by_category: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """카테고리별 뉴스 dict를 한 번의 AI 호출로 필터 (카테고리 구조 유지)"""
    flat = [it for items in news_by_category.values() for it in items]
    if not flat:
        return news_by_category
    relevant_ids = {id(it) for it in filter_relevant_ai(flat)}
    return {cat: [it for it in items if id(it) in relevant_ids]
            for cat, items in news_by_category.items()}
