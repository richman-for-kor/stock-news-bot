import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN, CHANNEL_ID, ADMIN_USER_ID
from db.users import init_db, add_user, is_approved, get_watchlist, add_watchlist, remove_watchlist
from scheduler import setup_scheduler, send_macro_and_sectors
from telegram_utils import send_html

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

HELP_TEXT = (
    "📈 <b>밍동의 부자되기</b> 주식 뉴스 봇\n\n"
    "<b>명령어</b>\n"
    "/dashboard — 거시경제 지표 + 섹터 분석\n"
    "/sectors — 섹터별 투자 환경만 보기\n"
    "/ai — AI·반도체 핵심 종목 시세\n"
    "/news — 지금 뉴스 요약 받기\n"
    "/watchlist — 저장된 관심 종목 분석\n"
    "/watchlist 삼성전자 — 특정 종목만 즉석 분석\n"
    "/watchlist add 삼성전자 엔비디아 SOXL — 추가(여러 개 OK)\n"
    "/watchlist del 삼성전자 — 삭제 · /watchlist clear — 전체삭제\n"
    "/invite — 채널 초대 링크 (관리자)\n"
    "/status — 봇 상태 (관리자)"
)


async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_approved(user.id):
        add_user(user.id, user.username or user.first_name, auto_approve=True)
    await send_html(context.bot, update.effective_chat.id,
                    f"안녕하세요, {user.first_name}님! 👋\n\n{HELP_TEXT}")


async def on_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_html(context.bot, update.effective_chat.id, HELP_TEXT)


async def on_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """초대 링크 발급 — 관리자만 가능"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ 관리자만 초대 링크를 발급할 수 있습니다.")
        return
    try:
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID, name="초대링크", creates_join_request=False,
        )
        await send_html(context.bot, update.effective_chat.id,
                        f"✅ <b>채널 초대 링크 발급됨</b>\n\n"
                        f"🔗 {link.invite_link}\n\n"
                        f"이 링크를 공유하면 채널에 참여할 수 있습니다.", preview=True)
    except Exception as e:
        await update.message.reply_text(f"❌ 링크 발급 실패: {e}")


async def on_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """거시경제 지표 + 섹터 분석 즉시 조회"""
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("📊 지표 수집 중...")
    try:
        await msg.delete()
    except Exception:
        pass
    try:
        await send_macro_and_sectors(context.bot, chat_id)
    except Exception as e:
        await send_html(context.bot, chat_id, f"❌ 오류: {e}")


async def on_sectors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """섹터별 투자 환경만 조회"""
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("🧭 섹터 분석 중...")
    try:
        from market.formatter import format_sector_message
        text = await asyncio.to_thread(format_sector_message)
        await msg.edit_text(text, parse_mode="HTML")
    except Exception as e:
        await msg.edit_text(f"❌ 오류: {e}")


async def on_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI/반도체 종목 시세 즉시 조회"""
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("🤖 시세 수집 중...")
    try:
        from market.formatter import format_bigtech_snapshot
        text = await asyncio.to_thread(format_bigtech_snapshot)
        await msg.edit_text(text, parse_mode="HTML")
    except Exception as e:
        await msg.edit_text(f"❌ 오류: {e}")


async def on_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지금 뉴스 요약 미리보기 (읽기 전용 — 채널 정시 요약에 영향 없음)"""
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("📰 뉴스 수집 중...")
    try:
        from news.collector import collect_all_news
        from news.formatter import format_hourly_summary
        news = await asyncio.to_thread(collect_all_news)
        text = format_hourly_summary(news) or "📭 새 뉴스가 없습니다."
        await msg.delete()
        await send_html(context.bot, chat_id, text)
    except Exception as e:
        await msg.edit_text(f"❌ 오류: {e}")


async def on_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /watchlist          — 현재 목록 분석
    /watchlist add NVDA 엔비디아  — 추가
    /watchlist del NVDA           — 삭제
    """
    chat_id = update.effective_chat.id
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ 관리자만 사용 가능합니다.")
        return

    args = context.args
    if args and args[0].lower() == "add":
        queries = [a.strip(",") for a in args[1:] if a.strip(",")]
        if not queries:
            await update.message.reply_text(
                "사용법: /watchlist add 종목명...\n"
                "예) /watchlist add 삼성전자 현대차 엔비디아 SOXL\n"
                "한글명·영문명·티커 모두 OK, 여러 개 한 번에 가능"
            )
            return
        msg = await update.message.reply_text("🔎 종목 검색 중...")
        from market.ticker_resolver import resolve_ticker
        resolved = await asyncio.gather(*[asyncio.to_thread(resolve_ticker, q) for q in queries])
        ok, fail = [], []
        for q, r in zip(queries, resolved):
            if r and r["symbol"]:
                add_watchlist(r["symbol"], r["name"])
                ok.append(f"✅ {r['name']} <i>({r['symbol']})</i>")
            else:
                fail.append(f"❓ {q}")
        lines = ["<b>관심 종목 추가 결과</b>", ""] + ok
        if fail:
            lines += ["", "<b>찾지 못함</b>"] + fail
        await msg.delete()
        await send_html(context.bot, chat_id, "\n".join(lines))
        return

    if args and args[0].lower() in ("del", "clear"):
        if args[0].lower() == "clear":
            from db.users import clear_watchlist
            clear_watchlist()
            await send_html(context.bot, chat_id, "🗑 관심 종목을 모두 비웠습니다.")
            return
        queries = [a.strip(",") for a in args[1:] if a.strip(",")]
        if not queries:
            await update.message.reply_text("사용법: /watchlist del 종목명\n전체 삭제: /watchlist clear")
            return
        from market.ticker_resolver import resolve_ticker
        removed = []
        for q in queries:
            r = await asyncio.to_thread(resolve_ticker, q)
            sym = r["symbol"] if r else q.upper()
            remove_watchlist(sym)
            removed.append(f"🗑 {q} <i>({sym})</i>")
        await send_html(context.bot, chat_id, "\n".join(["<b>삭제됨</b>", ""] + removed))
        return

    # add/del/clear가 아닌 인자 → 저장하지 않고 즉석 분석
    if args:
        queries = [a.strip(",") for a in args if a.strip(",")]
        msg = await update.message.reply_text("🔎 종목 검색·분석 중...")
        from market.ticker_resolver import resolve_ticker
        from market.analyst import analyze_items
        resolved = await asyncio.gather(*[asyncio.to_thread(resolve_ticker, q) for q in queries])
        items, notfound = [], []
        for q, r in zip(queries, resolved):
            if r and r["symbol"]:
                items.append({"ticker": r["symbol"], "name": r["name"]})
            else:
                notfound.append(q)
        try:
            await msg.delete()
        except Exception:
            pass
        if not items:
            await send_html(context.bot, chat_id, f"❓ 종목을 찾지 못했습니다: {', '.join(notfound)}")
            return
        text = await analyze_items(items, header="🔍 <b>즉석 종목 분석</b>")
        if notfound:
            text += f"\n\n<i>❓ 못 찾음: {', '.join(notfound)}</i>"
        await send_html(context.bot, chat_id, text)
        return

    # 인자 없음 → 저장된 관심 종목 전체 분석
    items = get_watchlist()
    if not items:
        await update.message.reply_text(
            "📋 관심 종목이 없습니다.\n\n"
            "즉석 분석: /watchlist 삼성전자\n"
            "추가: /watchlist add 삼성전자 엔비디아\n"
            "삭제: /watchlist del 삼성전자"
        )
        return

    msg = await update.message.reply_text("🤖 분석 중... (잠시 대기)")
    try:
        await msg.delete()
    except Exception:
        pass
    try:
        from market.analyst import analyze_watchlist
        text = await analyze_watchlist()
        await send_html(context.bot, chat_id, text)
    except Exception as e:
        await send_html(context.bot, chat_id, f"❌ 분석 오류: {e}")


async def on_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    scheduler = context.application.bot_data.get("scheduler")
    jobs = scheduler.get_jobs() if scheduler else []
    lines = ["✅ <b>봇 정상 동작 중</b>", "", "<b>예약된 작업</b>"]
    for j in jobs:
        nxt = j.next_run_time.strftime("%m/%d %H:%M") if j.next_run_time else "—"
        lines.append(f"• {j.id}: <i>{nxt}</i>")
    await send_html(context.bot, update.effective_chat.id, "\n".join(lines))


async def post_init(application: Application):
    init_db()
    scheduler = setup_scheduler(application.bot, CHANNEL_ID)
    scheduler.start()
    application.bot_data["scheduler"] = scheduler
    logging.info("스케줄러 시작 완료")


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",     on_start))
    app.add_handler(CommandHandler("help",      on_help))
    app.add_handler(CommandHandler("invite",    on_invite))
    app.add_handler(CommandHandler("dashboard", on_dashboard))
    app.add_handler(CommandHandler("sectors",   on_sectors))
    app.add_handler(CommandHandler("ai",        on_ai))
    app.add_handler(CommandHandler("news",      on_news))
    app.add_handler(CommandHandler("watchlist", on_watchlist))
    app.add_handler(CommandHandler("status",    on_status))
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
