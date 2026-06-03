"""
영문 → 한국어 번역 모듈
deep-translator (Google Translate 무료 API 사용)
"""
import re
from deep_translator import GoogleTranslator

_translator = GoogleTranslator(source="auto", target="ko")


def is_korean(text: str) -> bool:
    """한글 비율이 30% 이상이면 이미 한국어로 판단"""
    if not text:
        return True
    korean_chars = len(re.findall(r"[가-힣]", text))
    return (korean_chars / len(text)) >= 0.3


def translate(text: str) -> str:
    """영문이면 한국어로 번역, 이미 한국어면 그대로 반환"""
    if not text or is_korean(text):
        return text
    try:
        # 500자 초과 시 잘라서 번역
        if len(text) > 500:
            text = text[:500]
        return _translator.translate(text)
    except Exception:
        return text


def translate_item(item: dict) -> dict:
    """뉴스 아이템의 title, summary 번역"""
    return {
        **item,
        "title": translate(item.get("title", "")),
        "summary": translate(item.get("summary", "")) if item.get("summary") else "",
    }


def translate_items(items: list[dict]) -> list[dict]:
    return [translate_item(item) for item in items]
