"""
AI 텍스트 생성 — Gemini 전용 (무료 티어)
Termux 호환을 위해 SDK 없이 requests로 REST API를 직접 호출한다.
"""
import os
import re
import time
import requests

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def clean_ai_markdown(text: str) -> str:
    """AI가 반환한 마크다운을 텔레그램 HTML로 변환 + 가독성 정리"""
    if not text:
        return ""
    t = text.strip()
    # HTML 특수문자 이스케이프 (AI 원문 보호)
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # 헤더(#, ##, ###) → 굵게 (앞에 빈 줄로 구분)
    t = re.sub(r"(?m)^\s*#{1,6}\s*(.+?)\s*$", r"\n<b>\1</b>", t)
    # **굵게** → <b>
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    # 줄머리 불릿(-, *, •) → •
    t = re.sub(r"(?m)^\s*[-*•]\s+", "• ", t)
    # 남은 단독 * 제거
    t = t.replace("*", "")
    # 과한 빈 줄 정리 (3줄 이상 → 2줄)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def ai_available() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def ai_generate(prompt: str, max_tokens: int = 700) -> str:
    """Gemini로 텍스트 생성. 무료 한도(429)·네트워크 오류 시 백오프 재시도.
    최종 실패 시 예외 발생 → 호출부에서 규칙 기반 폴백."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 미설정")

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.6,
            # 2.5 계열 thinking 모델이 추론에 출력 토큰을 소진해 빈 응답 내는 것 방지
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    url = GEMINI_ENDPOINT.format(model=_gemini_model())

    last_err = None
    # 첫 시도 즉시, 이후 백오프(무료 분당 한도 회복 대기)
    for delay in (0, 6, 14):
        if delay:
            time.sleep(delay)
        try:
            r = requests.post(url, params={"key": key}, json=body, timeout=30)
        except Exception as e:
            last_err = e  # 네트워크/타임아웃 → 재시도
            continue
        if r.status_code == 429:
            last_err = RuntimeError("RATE_LIMIT")  # 무료 한도 → 백오프 후 재시도
            continue
        r.raise_for_status()  # 그 외 4xx/5xx는 즉시 중단
        j = r.json()
        raw = j["candidates"][0]["content"]["parts"][0]["text"]
        return clean_ai_markdown(raw)

    raise last_err or RuntimeError("AI 생성 실패")
