"""
텔레그램 발송 공통 유틸
- 4096자 제한 자동 분할 발송
- HTML 파싱 실패 시 평문으로 폴백
"""
import logging

log = logging.getLogger(__name__)

MAX_LEN = 3900  # 4096 여유분


def _split_text(text: str, max_len: int = MAX_LEN) -> list[str]:
    """긴 텍스트를 줄 단위로 안전하게 분할 (구분선/문단 우선)"""
    if len(text) <= max_len:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        # 한 줄 자체가 너무 길면 강제로 자른다
        while len(line) > max_len:
            chunks.append(line[:max_len])
            line = line[max_len:]
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


async def send_html(bot, chat_id, text: str, preview: bool = False):
    """HTML 메시지를 4096자 제한에 맞춰 분할 발송. 실패 시 평문 폴백."""
    if not text or not text.strip():
        return
    for chunk in _split_text(text):
        try:
            await bot.send_message(
                chat_id=chat_id, text=chunk,
                parse_mode="HTML", disable_web_page_preview=not preview,
            )
        except Exception as e:
            log.warning(f"HTML 발송 실패, 평문 재시도: {e}")
            try:
                # HTML 태그 제거 후 평문 발송
                import re
                plain = re.sub(r"<[^>]+>", "", chunk)
                await bot.send_message(
                    chat_id=chat_id, text=plain,
                    disable_web_page_preview=not preview,
                )
            except Exception as e2:
                log.error(f"평문 발송도 실패: {e2}")
