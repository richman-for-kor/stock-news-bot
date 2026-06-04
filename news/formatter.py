from datetime import datetime
import pytz

KST = pytz.timezone("Asia/Seoul")


def _e(text: str) -> str:
    """HTML 특수문자 이스케이프"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_breaking(item: dict) -> str:
    title = _e(item.get("title", ""))
    source = _e(item.get("source", ""))
    category = _e(item.get("category", ""))
    link = item.get("link", "")
    ai_summary = item.get("ai_summary")  # ai_generate 결과 — 이미 HTML 안전, 재이스케이프 금지
    parts = [f"🚨 <b>속보 · {category}</b>", "", f'<a href="{link}">{title}</a>']
    if ai_summary:
        parts += ["", f"📝 {ai_summary}"]
    elif item.get("summary"):
        parts += ["", _e(item["summary"])]
    parts += ["", f"📡 {source}"]
    return "\n".join(parts)


def format_hourly_summary(news_by_category: dict[str, list[dict]]) -> str:
    now = datetime.now(KST).strftime("%m/%d %H:%M")
    lines = [f"📰 <b>뉴스 요약</b>  <i>{now} KST</i>"]

    has_any = False
    for category, items in news_by_category.items():
        if not items:
            continue
        has_any = True
        emoji = {"한국증시": "🇰🇷", "미국증시": "🇺🇸", "암호화폐": "₿"}.get(category, "📌")
        lines.append(f"\n{emoji} <b>{category}</b>")
        for item in items[:5]:
            title = _e(item.get("title", ""))
            link = item.get("link", "")
            lines.append(f'• <a href="{link}">{title}</a>')

    if not has_any:
        return ""
    return "\n".join(lines)


def format_market_briefing(market: str) -> str:
    now = datetime.now(KST).strftime("%H:%M")
    if market == "korean":
        return (
            f"🇰🇷 <b>국장 개장 브리핑</b>  <i>{now} KST</i>\n\n"
            f"⏰ 1시간 후 개장 — 08:00 <i>(NXT 포함, 20:30 마감)</i>\n\n"
            f"📋 체크포인트\n"
            f"• 전일 미국 증시 마감 동향\n"
            f"• 야간 선물·환율 흐름\n"
            f"• 외국인 수급 방향"
        )
    else:
        return (
            f"🇺🇸 <b>미장 개장 브리핑</b> — {now}\n\n"
            f"⏰ 1시간 후 미국 증시 개장 (09:30 ET)\n\n"
            f"주요 체크포인트:\n"
            f"• 선물 지수 (S&P500, NASDAQ, DOW)\n"
            f"• 유럽 증시 마감 동향\n"
            f"• 주요 경제 지표 발표 여부\n\n"
            f"📊 오늘의 미국 증시 뉴스를 확인하세요."
        )
