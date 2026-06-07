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


# 폴백용 태그 추정 사전 (구체적 종목 → 섹터 순). 위에서부터 먼저 매칭.
_TAG_MAP = [
    ("삼성전자", ["삼성전자", "samsung electronics"]),
    ("SK하이닉스", ["하이닉스", "sk hynix", "hynix"]),
    ("엔비디아", ["엔비디아", "nvidia", "nvda"]),
    ("테슬라", ["테슬라", "tesla", "tsla"]),
    ("애플", ["애플", "apple", "aapl"]),
    ("현대차", ["현대차", "hyundai motor"]),
    ("TSMC", ["tsmc"]),
    ("비트코인", ["비트코인", "bitcoin", "btc"]),
    ("이더리움", ["이더리움", "ethereum"]),
    ("리플", ["리플", "xrp"]),
    ("나스닥", ["나스닥", "nasdaq"]),
    ("S&P500", ["s&p", "sp500", "에스앤피"]),
    ("다우", ["다우", "dow jones", "다우존스"]),
    ("코스피", ["코스피", "kospi"]),
    ("코스닥", ["코스닥", "kosdaq"]),
    ("금", ["금값", "gold", "금 가격"]),
    ("유가", ["유가", "crude", "브렌트", "oil price"]),
    ("원/달러", ["원/달러", "환율", "원달러"]),
    ("국채금리", ["국채", "treasury", "10년물"]),
    ("반도체", ["반도체", "hbm", "semiconductor"]),
    ("2차전지", ["2차전지", "배터리"]),
    ("바이오", ["바이오", "제약"]),
    ("방산", ["방산", "방위산업"]),
]


def guess_tag(item: dict) -> str | None:
    """알려진 종목/지수/자산명을 헤드라인에서 찾아 태그 추정 (AI 폴백용)"""
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    for tag, pats in _TAG_MAP:
        if any(p in text for p in pats):
            return tag
    return None


# ── AI 기반 관련성 필터 (배치 1회 호출) ─────────────
def _keyword_fallback(items: list[dict]) -> list[dict]:
    kept = filter_relevant(items)
    for it in kept:
        it["tag"] = guess_tag(it)
    return kept


def filter_relevant_ai(items: list[dict]) -> list[dict]:
    """Gemini가 증시 관련 뉴스만 선별 + 관련 종목/지수 태그까지 한 번에. 실패 시 키워드 폴백."""
    if not items:
        return []
    import re
    import html as _html
    from market.ai_client import ai_available, ai_generate

    if not ai_available():
        return _keyword_fallback(items)

    numbered = "\n".join(f"{i+1}. {it.get('title','')}" for i, it in enumerate(items))
    prompt = (
        "아래는 뉴스 헤드라인 목록입니다. 이 중 '주식·증시·시장에 실제로 "
        "영향을 주거나 시장/종목/거시경제 동향을 다루는' 뉴스만 고르고, "
        "각 뉴스에 '직접 관련된' 대상을 한 단어 태그로 붙이세요.\n"
        "제외 대상: 정치 가십, 사건사고, 연예·스포츠·날씨, 단순 행사/홍보/채용, "
        "인물 일상, 노조·내부 이슈 등 시장과 직접 무관한 것.\n\n"
        "태그 규칙(중요):\n"
        "- 헤드라인에 직접 등장하거나 직접 영향받는 대상만 태그로. "
        "종목명(삼성전자·엔비디아), 지수(코스피·나스닥), 자산(비트코인·금·유가·원/달러) 등.\n"
        "- 한국 기업/이슈면 한국 대상, 미국/글로벌이면 미국 대상으로 정확히. "
        "미국 기사에 코스피를 붙이지 마세요.\n"
        "- 특정 대상이 분명하지 않거나 막연히 '시장 전체'면 억지로 붙이지 말고 태그를 '-' 로.\n\n"
        f"{numbered}\n\n"
        "형식: '번호. 태그' 한 줄씩. 관련 없으면 그 번호는 빼고, "
        "관련은 있지만 특정 대상이 없으면 '-'.\n예)\n1. 삼성전자\n4. 나스닥\n7. -"
    )
    try:
        resp = ai_generate(prompt, max_tokens=500)
        mapping = {}
        for line in resp.splitlines():
            m = re.match(r"\s*(\d+)\s*[.)]\s*(.+)", line)
            if m:
                # ai_generate가 이스케이프해 둔 태그를 평문으로 되돌림(표시 시 1회만 이스케이프)
                tag = _html.unescape(m.group(2).strip())
                if tag in ("-", "—", "없음", "N/A", "n/a"):
                    tag = None          # 막연한 경우 태그 생략
                mapping[int(m.group(1))] = tag
        if not mapping:                    # 파싱 실패 → 키워드 폴백
            return _keyword_fallback(items)
        result = []
        for idx, tag in sorted(mapping.items()):
            if 1 <= idx <= len(items):
                it = items[idx - 1]
                it["tag"] = tag
                result.append(it)
        return result
    except Exception:
        return _keyword_fallback(items)    # AI 오류 → 키워드 폴백


def filter_news_by_category_ai(news_by_category: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """카테고리별 뉴스 dict를 한 번의 AI 호출로 필터 (카테고리 구조 유지)"""
    flat = [it for items in news_by_category.values() for it in items]
    if not flat:
        return news_by_category
    relevant_ids = {id(it) for it in filter_relevant_ai(flat)}
    return {cat: [it for it in items if id(it) in relevant_ids]
            for cat, items in news_by_category.items()}
