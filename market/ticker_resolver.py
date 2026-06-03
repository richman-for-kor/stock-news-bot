"""
종목명 → Yahoo 티커 자동 변환
네이버 증권 자동완성 API 사용 (한글명·영문명·티커 모두 인식)
- 국내: 005930 + KOSPI → 005930.KS / KOSDAQ → .KQ
- 해외: NVDA → NVDA 그대로
"""
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}


def resolve_ticker(query: str) -> dict | None:
    """검색어를 Yahoo 심볼로 변환. 반환: {symbol, name, market} 또는 None"""
    query = query.strip().strip(",").strip()
    if not query:
        return None
    try:
        r = requests.get(
            "https://ac.stock.naver.com/ac",
            params={"q": query, "target": "stock,index,etf"},
            headers=HEADERS, timeout=8,
        )
        items = r.json().get("items", [])
    except Exception:
        items = []

    if items:
        it = items[0]
        code = it.get("code", "")
        name = it.get("name", query)
        type_code = it.get("typeCode", "")
        nation = it.get("nationCode", "")

        if nation == "KOR":
            if type_code == "KOSPI":
                return {"symbol": f"{code}.KS", "name": name, "market": "KOSPI"}
            if type_code == "KOSDAQ":
                return {"symbol": f"{code}.KQ", "name": name, "market": "KOSDAQ"}
            # 지수 등 기타 국내
            return {"symbol": f"{code}.KS", "name": name, "market": type_code}
        else:
            # 해외 주식/ETF: 네이버 code가 곧 티커
            return {"symbol": code, "name": name, "market": type_code}

    # 네이버가 못 찾으면 입력값을 그대로 티커로 간주 (예: 사용자가 005930.KS 직접 입력)
    return {"symbol": query.upper(), "name": query.upper(), "market": ""}
