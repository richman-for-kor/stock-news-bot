"""
거시경제 지표 기반 섹터 분석
현재 매크로 환경에서 어떤 섹터가 유리/불리한지 AI + 규칙 기반으로 판단
"""
import os
from market.indicators import get_all_indicators

SECTORS = [
    "반도체/AI",
    "소비재(경기민감)",
    "필수소비재(음식·생활)",
    "로봇·자동화",
    "항공·우주·방산",
    "에너지(원유·가스)",
    "금융·은행",
    "헬스케어·바이오",
    "신재생에너지",
    "부동산(리츠)",
]


def _build_macro_summary(indicators: dict) -> str:
    """지표 딕셔너리를 텍스트 요약으로 변환"""
    lines = []
    name_map = {
        "TNX":    "미국 10년물 국채금리(%)",
        "TYX":    "미국 30년물 국채금리(%)",
        "VIX":    "공포지수 VIX",
        "BRENT":  "브렌트유($)",
        "GOLD":   "금($)",
        "DXY":    "달러 인덱스",
        "KRW":    "원/달러 환율",
        "SP500":  "S&P500",
        "NASDAQ": "NASDAQ",
        "KOSPI":  "KOSPI",
    }
    for key, name in name_map.items():
        info = indicators.get(key, {})
        price = info.get("price")
        is_alert = info.get("is_alert", False)
        val = f"{price:,.2f}" if price else "N/A"
        alert_tag = " ⚠️경고" if is_alert else ""
        lines.append(f"- {name}: {val}{alert_tag}")
    return "\n".join(lines)


def analyze_sectors_ai(indicators: dict) -> str:
    """AI로 섹터별 투자 신호 분석"""
    from market.ai_client import ai_generate
    macro_text = _build_macro_summary(indicators)

    sectors = chr(10).join(f"- {s}" for s in SECTORS)
    prompt = f"""당신은 거시경제 전문 투자 애널리스트입니다.
아래 거시경제 지표를 바탕으로 섹터별 투자 환경을 분석하세요.

거시경제 지표:
{macro_text}

분석할 섹터:
{sectors}

⚠️ 출력 형식 규칙 (반드시 지킬 것):
- 마크다운 기호(#, *, **) 절대 사용 금지. 일반 텍스트로만.
- 맨 위에 2~3문장으로 '총평'을 쓰고, 그 뒤에 빈 줄 한 줄.
- 그다음 각 섹터를 한 줄씩, 아래 형식으로:
  섹터명 — 🟢매수우호 / 🟡중립관망 / 🔴위험주의 중 하나 — 근거 1문장
- 섹터 목록이 끝나면 빈 줄 한 줄 후, 아래 두 줄 추가:
  💡 주목 섹터: (1~2개)
  ⚠️ 주의 섹터: (1~2개)

한국어로, 간결하게 답변하세요."""

    return ai_generate(prompt, max_tokens=1000)


def analyze_sectors_rule(indicators: dict) -> str:
    """규칙 기반 섹터 분석 — AI 폴백"""
    tnx   = (indicators.get("TNX",  {}).get("price") or 0)
    vix   = (indicators.get("VIX",  {}).get("price") or 0)
    brent = (indicators.get("BRENT",{}).get("price") or 0)
    dxy   = (indicators.get("DXY",  {}).get("price") or 0)
    krw   = (indicators.get("KRW",  {}).get("price") or 0)

    high_rate   = tnx >= 4.5
    high_fear   = vix >= 30
    high_oil    = brent >= 85
    strong_dxy  = dxy >= 105
    weak_krw    = krw >= 1400

    results = []
    for sector in SECTORS:
        if sector == "반도체/AI":
            if high_rate and high_fear:
                sig = "🔴위험주의 — 고금리+공포지수 상승으로 성장주 압박"
            elif not high_rate:
                sig = "🟢매수우호 — 금리 안정, AI 수요 견조"
            else:
                sig = "🟡중립관망 — 금리 부담 있으나 AI 모멘텀 유지"

        elif sector == "소비재(경기민감)":
            if high_fear or high_rate:
                sig = "🔴위험주의 — 경기 둔화 우려, 소비 위축 가능"
            else:
                sig = "🟡중립관망 — 경기 상황 모니터링 필요"

        elif sector == "필수소비재(음식·생활)":
            if high_fear:
                sig = "🟢매수우호 — 공포 구간 방어주 선호"
            else:
                sig = "🟡중립관망 — 안정적이나 성장성 제한"

        elif sector == "로봇·자동화":
            if not high_rate:
                sig = "🟢매수우호 — 금리 안정시 성장주 수혜"
            elif high_rate and high_fear:
                sig = "🔴위험주의 — 고금리 환경 성장주 불리"
            else:
                sig = "🟡중립관망 — 장기 트렌드 유효, 단기 변동성"

        elif sector == "항공·우주·방산":
            if high_oil:
                sig = "🔴위험주의 — 고유가로 항공 비용 증가"
            else:
                sig = "🟢매수우호 — 지정학 긴장 지속, 방산 수요 증가"

        elif sector == "에너지(원유·가스)":
            if high_oil:
                sig = "🟢매수우호 — 고유가 수혜 섹터"
            else:
                sig = "🟡중립관망 — 유가 방향성 확인 필요"

        elif sector == "금융·은행":
            if high_rate:
                sig = "🟢매수우호 — 고금리 환경 순이자마진 확대"
            else:
                sig = "🟡중립관망 — 금리 하락 시 마진 압박"

        elif sector == "헬스케어·바이오":
            if high_fear:
                sig = "🟢매수우호 — 경기 방어주, 변동성 구간 유리"
            else:
                sig = "🟡중립관망 — 규제 리스크 상존"

        elif sector == "신재생에너지":
            if high_rate:
                sig = "🔴위험주의 — 고금리로 자본비용 증가, 투자 위축"
            else:
                sig = "🟢매수우호 — 정책 수혜 지속"

        elif sector == "부동산(리츠)":
            if high_rate:
                sig = "🔴위험주의 — 고금리로 이자비용 증가, 배당 매력 감소"
            else:
                sig = "🟢매수우호 — 금리 하락 시 강한 수혜"
        else:
            sig = "🟡중립관망"

        results.append(f"• {sector} — {sig}")

    return "\n".join(results)


def get_sector_analysis(indicators: dict | None = None) -> str:
    """AI + 규칙 기반 섹터 분석 통합 (지표를 넘기면 재조회 생략)"""
    if indicators is None:
        indicators = get_all_indicators()

    try:
        ai_result = analyze_sectors_ai(indicators)
        return f"🧭 <b>섹터별 투자 환경</b>  <i>AI 분석</i>\n\n{ai_result}"
    except Exception:
        rule_result = analyze_sectors_rule(indicators)
        return f"🧭 <b>섹터별 투자 환경</b>  <i>규칙 기반</i>\n\n{rule_result}"
