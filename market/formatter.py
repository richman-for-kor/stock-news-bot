"""거시경제 지표 메시지 포매터 (HTML)"""
from datetime import datetime
import pytz
from market.indicators import (
    get_all_indicators, get_bigtech_prices, check_red_alerts,
    format_price, format_change,
)
from market.sector_analyst import get_sector_analysis

KST = pytz.timezone("Asia/Seoul")


def _fmt(price, decimals=2, suffix=""):
    if price is None:
        return "N/A"
    return f"{price:,.{decimals}f}{suffix}"


def format_macro_dashboard(ind: dict | None = None) -> str:
    """거시경제 핵심 지표 — 절대 신호등 + 주요 지표 (올바른 키 사용)"""
    if ind is None:
        ind = get_all_indicators()
    now = datetime.now(KST).strftime("%m/%d %H:%M")
    lines = [f"📊 <b>거시경제 대시보드</b>  <i>{now} KST</i>", ""]

    # 절대 신호등 — 임계값 기준 경보
    lines.append("🚦 <b>절대 신호등</b>")
    signal_rows = [
        ("TNX",   "미국 10년물", "%",   "4.5"),
        ("KRW",   "원/달러",     "원",  "1,450"),
        ("BRENT", "브렌트유",     "$",  "100"),
        ("VIX",   "공포지수",     "",    "40"),
    ]
    for key, label, unit, thr in signal_rows:
        info = ind.get(key, {})
        price = info.get("price")
        is_alert = info.get("is_alert", False)
        dot = "🔴" if is_alert else "🟢"
        if price is None:
            val = "N/A"
        elif unit == "원":
            val = f"{int(price):,}원"
        elif unit == "$":
            val = f"${price:,.2f}"
        elif unit == "%":
            val = f"{price:.2f}%"
        else:
            val = f"{price:,.2f}"
        chg = format_change(info.get("change_pct"))
        chg_part = f" {chg}" if chg else ""
        warn = " ⚠️" if is_alert else ""
        lines.append(f"{dot} {label} <b>{val}</b>{chg_part} <i>(기준 {thr}{unit})</i>{warn}")

    # 주요 지수 — 등락률 포함
    lines.append("")
    lines.append("📈 <b>주요 지수</b>")
    index_rows = [
        ("SP500",  "S&P 500"),
        ("NASDAQ", "나스닥"),
        ("KOSPI",  "코스피"),
    ]
    for key, label in index_rows:
        info = ind.get(key, {})
        price = info.get("price")
        chg = format_change(info.get("change_pct"))
        lines.append(f"• {label}: <b>{_fmt(price)}</b> {chg}")

    # 기타 거시 지표
    lines.append("")
    lines.append("🌐 <b>거시 지표</b>")
    macro_rows = [
        ("TYX",  "미국 30년물", "%"),
        ("GOLD", "금(Gold)",   "$"),
        ("DXY",  "달러인덱스",  ""),
    ]
    for key, label, unit in macro_rows:
        info = ind.get(key, {})
        price = info.get("price")
        if price is None:
            val = "N/A"
        elif unit == "%":
            val = f"{price:.2f}%"
        elif unit == "$":
            val = f"${price:,.2f}"
        else:
            val = f"{price:,.2f}"
        chg = format_change(info.get("change_pct"))
        lines.append(f"• {label}: <b>{val}</b> {chg}".rstrip())

    return "\n".join(lines)


def format_sector_message(ind: dict | None = None) -> str:
    """섹터별 투자 환경 분석 (별도 메시지)"""
    return get_sector_analysis(ind)


def format_bigtech_snapshot() -> str:
    data = get_bigtech_prices()
    lines = ["🤖 <b>AI·반도체 핵심 종목</b>", ""]
    for ticker, info in data.items():
        val = format_price(ticker, info["price"])
        lines.append(f"• {info['name']}: <b>{val}</b>  <i>{ticker}</i>")
    return "\n".join(lines)


def format_red_alert(alerts: list[dict]) -> str:
    lines = ["🚨🚨 <b>긴급: 절대 신호등 돌파!</b> 🚨🚨", ""]
    for a in alerts:
        if a["unit"] == "원":
            cur = f"{int(a['price']):,}원"
        elif a["unit"] == "$":
            cur = f"${a['price']:,.2f}"
        elif a["unit"] == "%":
            cur = f"{a['price']:.2f}%"
        else:
            cur = f"{a['price']:,.2f}"
        lines.append(f"{a['emoji']} <b>{a['name']}</b>")
        lines.append(f"    현재 <b>{cur}</b> · 기준 {a['threshold']}{a['unit']}")
    lines.append("")
    lines.append("⚠️ 퀄리티 자산(M7·방산·에너지) 또는 현금 비중 점검 권장")
    return "\n".join(lines)
