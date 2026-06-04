"""
속보 AI 요약 — 제목·본문을 받아 한국어 2~3문장으로 압축.
ai_generate가 이미 HTML 안전 문자열을 반환하므로, 호출부에서 재이스케이프하지 말 것.
"""


def ai_summarize(item: dict) -> str | None:
    """뉴스 아이템을 2~3문장 한국어 요약으로. 실패/AI없음 시 None."""
    from market.ai_client import ai_available, ai_generate
    if not ai_available():
        return None

    title = (item.get("title") or "").strip()
    body = (item.get("summary") or "").strip()
    if not title and not body:
        return None

    prompt = (
        "다음 뉴스를 한국어로 2~3문장으로 간결하게 요약하세요. "
        "핵심 사실과 시장에 주는 영향 위주로, 인사말·군더더기 없이 요약문만 출력하세요.\n\n"
        f"제목: {title}\n"
        f"내용: {body if body else '(본문 없음 — 제목 기준으로 요약)'}"
    )
    try:
        text = ai_generate(prompt, max_tokens=200)
        return text or None
    except Exception:
        return None
