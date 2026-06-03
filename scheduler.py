from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio
import pytz
import logging

from news.collector import collect_all_news, collect_breaking_news
from news.crawler import crawl_all_news
from news.formatter import format_hourly_summary, format_breaking, format_market_briefing
from market.analyst import analyze_watchlist
from market.indicators import check_red_alerts, get_all_indicators, _yahoo_quote, format_change
from market.formatter import (
    format_macro_dashboard, format_sector_message,
    format_bigtech_snapshot, format_red_alert,
)
from market.schedule_helper import get_us_briefing_time, get_us_close_time, get_market_status, is_us_dst
from config import BREAKING_KEYWORDS
from db.users import mark_news_sent, is_news_sent
from telegram_utils import send_html

KST = pytz.timezone("Asia/Seoul")
log = logging.getLogger(__name__)


# ────────────────────────────────────────────────
# 공통: 거시 대시보드 + 섹터 분석 (지표 1회 조회 공유)
# ────────────────────────────────────────────────
async def send_macro_and_sectors(bot, channel_id: str, with_sectors: bool = True):
    ind = await asyncio.to_thread(get_all_indicators)
    await send_html(bot, channel_id, format_macro_dashboard(ind))
    if with_sectors:
        sector_text = await asyncio.to_thread(format_sector_message, ind)
        await send_html(bot, channel_id, sector_text)


async def send_watchlist(bot, channel_id: str):
    text = await analyze_watchlist()
    if text:
        await send_html(bot, channel_id, text)


# ────────────────────────────────────────────────
# 속보 / 정시 뉴스
# ────────────────────────────────────────────────
async def send_breaking_news(bot, channel_id: str):
    """속보 감지 + 크롤링 속보 — 5분마다 (사전 필터는 원문, 매칭만 번역)"""
    breaking = await asyncio.to_thread(collect_breaking_news)
    for item in breaking:
        await send_html(bot, channel_id, format_breaking(item), preview=True)
        mark_news_sent(item["link"])

    # 크롤링 뉴스: 번역 없이 받아 속보 키워드만 검사 후, 매칭 건만 번역
    crawled = await crawl_all_news(translate=False)
    from news.translator import translate_item
    for item in crawled:
        if item["link"] and not is_news_sent(item["link"]):
            if any(kw.lower() in item["title"].lower() for kw in BREAKING_KEYWORDS):
                tr = await asyncio.to_thread(translate_item, item)
                await send_html(bot, channel_id, format_breaking({**tr, "category": tr["source"]}))
                mark_news_sent(item["link"])


async def send_hourly_summary(bot, channel_id: str):
    """매 정시 뉴스 요약 + 크롤링 뉴스"""
    news = await asyncio.to_thread(collect_all_news)
    for items in news.values():
        for item in items:
            mark_news_sent(item["link"])
    text = format_hourly_summary(news)
    await send_html(bot, channel_id, text)

    crawled = await crawl_all_news()
    new_items = [i for i in crawled if i["link"] and not is_news_sent(i["link"])]
    if new_items:
        lines = ["📰 <b>크롤링 뉴스</b>", ""]
        for item in new_items[:8]:
            title = item["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f'• <a href="{item["link"]}">{title}</a>  <i>{item["source"]}</i>')
            mark_news_sent(item["link"])
        await send_html(bot, channel_id, "\n".join(lines))


async def send_red_alert_check(bot, channel_id: str):
    """절대 신호등 임계값 체크 — 15분마다"""
    try:
        alerts = await asyncio.to_thread(check_red_alerts)
        if alerts:
            await send_html(bot, channel_id, format_red_alert(alerts))
    except Exception as e:
        log.warning(f"신호등 체크 오류: {e}")


# ────────────────────────────────────────────────
# 개장/마감 브리핑
# ────────────────────────────────────────────────
async def send_korean_briefing(bot, channel_id: str):
    """07:00 KST — 국장 개장 1시간 전 브리핑"""
    await send_html(bot, channel_id, format_market_briefing("korean"))
    try:
        await send_macro_and_sectors(bot, channel_id)
        await send_watchlist(bot, channel_id)
    except Exception as e:
        log.warning(f"국장 브리핑 오류: {e}")
    await send_hourly_summary(bot, channel_id)


async def send_us_briefing(bot, channel_id: str):
    """미장 개장 1시간 전 브리핑 — DST 자동 반영"""
    dst = is_us_dst()
    open_time = "22:30 KST" if dst else "23:30 KST"
    dst_label = "EDT 써머타임" if dst else "EST 표준시"
    now = datetime.now(KST).strftime("%H:%M")
    text = (
        f"🇺🇸 <b>미장 개장 브리핑</b>  <i>{now} KST</i>\n\n"
        f"⏰ 1시간 후 개장 — {open_time} <i>({dst_label})</i>\n\n"
        f"📋 체크포인트\n"
        f"• 선물 지수 (S&P500·나스닥·다우)\n"
        f"• 유럽 증시 마감 동향\n"
        f"• 주요 경제 지표 발표 일정"
    )
    await send_html(bot, channel_id, text)
    try:
        await send_macro_and_sectors(bot, channel_id)
        await send_html(bot, channel_id, await asyncio.to_thread(format_bigtech_snapshot))
        await send_watchlist(bot, channel_id)
    except Exception as e:
        log.warning(f"미장 브리핑 오류: {e}")
    await send_hourly_summary(bot, channel_id)


async def send_korean_close(bot, channel_id: str):
    """20:30 KST — 국장 마감 브리핑"""
    now = datetime.now(KST).strftime("%Y-%m-%d")
    try:
        kospi = await asyncio.to_thread(_yahoo_quote, "^KS11")
        kosdaq = await asyncio.to_thread(_yahoo_quote, "^KQ11")
        kospi_line = f"{kospi['price']:,.2f} {format_change(kospi['change_pct'])}" if kospi["price"] else "N/A"
        kosdaq_line = f"{kosdaq['price']:,.2f} {format_change(kosdaq['change_pct'])}" if kosdaq["price"] else "N/A"
    except Exception:
        kospi_line = kosdaq_line = "N/A"

    text = (
        f"🇰🇷 <b>국장 마감 브리핑</b>  <i>{now}</i>\n\n"
        f"📊 마감 지수\n"
        f"• 코스피: <b>{kospi_line}</b>\n"
        f"• 코스닥: <b>{kosdaq_line}</b>\n\n"
        f"📋 체크포인트\n"
        f"• 외국인·기관 수급 동향\n"
        f"• 오늘의 테마·주도주\n"
        f"• 내일 주목할 이슈"
    )
    await send_html(bot, channel_id, text)
    try:
        await send_watchlist(bot, channel_id)
    except Exception as e:
        log.warning(f"국장 마감 관심종목 오류: {e}")
    await send_hourly_summary(bot, channel_id)


async def send_us_close(bot, channel_id: str):
    """미장 마감 브리핑 — DST 자동 반영"""
    dst = is_us_dst()
    close_time = "05:00 KST (EDT)" if dst else "06:00 KST (EST)"
    now = datetime.now(KST).strftime("%Y-%m-%d")
    try:
        ind = await asyncio.to_thread(get_all_indicators)
        def line(key, label):
            info = ind.get(key, {})
            p = info.get("price")
            if p is None:
                return f"• {label}: N/A"
            return f"• {label}: <b>{p:,.2f}</b> {format_change(info.get('change_pct'))}"
        idx_block = "\n".join([
            line("SP500", "S&P 500"),
            line("NASDAQ", "나스닥"),
            line("VIX", "VIX(공포)"),
            line("DXY", "달러인덱스"),
        ])
    except Exception:
        ind = None
        idx_block = "지수 조회 실패"

    text = (
        f"🇺🇸 <b>미장 마감 브리핑</b>  <i>{now}</i>\n\n"
        f"⏰ 마감 — {close_time}\n\n"
        f"📊 마감 지수\n{idx_block}\n\n"
        f"📋 체크포인트\n"
        f"• 섹터별 등락 흐름\n"
        f"• 국채 금리·달러 동향\n"
        f"• 내일 국장에 미칠 영향"
    )
    await send_html(bot, channel_id, text)
    try:
        if ind is not None:
            await send_html(bot, channel_id, await asyncio.to_thread(format_sector_message, ind))
        await send_watchlist(bot, channel_id)
    except Exception as e:
        log.warning(f"미장 마감 오류: {e}")
    await send_hourly_summary(bot, channel_id)


async def reschedule_us_briefing(scheduler: AsyncIOScheduler, bot, channel_id: str):
    """DST 변경 시 미장 브리핑/마감 시각 재등록 — 매일 새벽 3시 체크"""
    us_hour, us_min = get_us_briefing_time()
    us_close_h, us_close_m = get_us_close_time()
    status = get_market_status()
    label = "EDT 써머타임" if status["us_dst"] else "EST 표준시"
    try:
        scheduler.reschedule_job("us_briefing",
                                 trigger=CronTrigger(hour=us_hour, minute=us_min, timezone=KST))
        scheduler.reschedule_job("us_close",
                                 trigger=CronTrigger(hour=us_close_h, minute=us_close_m, timezone=KST))
        log.info(f"미장 시각 재조정 ({label}): 브리핑 {status['us_briefing_kst']}, 마감 {status['us_close_kst']}")
    except Exception as e:
        log.warning(f"스케줄 재조정 오류: {e}")


def setup_scheduler(bot, channel_id: str) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=KST)

    scheduler.add_job(send_breaking_news, "interval", minutes=5,
                      args=[bot, channel_id], id="breaking_news")
    scheduler.add_job(send_red_alert_check, "interval", minutes=15,
                      args=[bot, channel_id], id="red_alert_check")
    scheduler.add_job(send_hourly_summary, CronTrigger(minute=0, timezone=KST),
                      args=[bot, channel_id], id="hourly_summary")
    # 국장 개장 07:00 / 마감 20:30
    scheduler.add_job(send_korean_briefing, CronTrigger(hour=7, minute=0, timezone=KST),
                      args=[bot, channel_id], id="korean_briefing")
    scheduler.add_job(send_korean_close, CronTrigger(hour=20, minute=30, timezone=KST),
                      args=[bot, channel_id], id="korean_close")

    # 미장 개장/마감 — DST 자동 감지
    us_hour, us_min = get_us_briefing_time()
    us_close_h, us_close_m = get_us_close_time()
    status = get_market_status()
    log.info(f"미장 등록: 브리핑 {status['us_briefing_kst']} / 마감 {status['us_close_kst']} "
             f"({'DST' if status['us_dst'] else 'EST'})")
    scheduler.add_job(send_us_briefing, CronTrigger(hour=us_hour, minute=us_min, timezone=KST),
                      args=[bot, channel_id], id="us_briefing")
    scheduler.add_job(send_us_close, CronTrigger(hour=us_close_h, minute=us_close_m, timezone=KST),
                      args=[bot, channel_id], id="us_close")

    # DST 변경 감지: 매일 새벽 3시
    scheduler.add_job(reschedule_us_briefing, CronTrigger(hour=3, minute=0, timezone=KST),
                      args=[scheduler, bot, channel_id], id="dst_check")

    return scheduler
