"""
시장 개장 시간 동적 계산
- 미국 DST(써머타임) 자동 감지
- 한국 NXT 야간 세션 지원
"""
from datetime import datetime
import pytz

KST = pytz.timezone("Asia/Seoul")
US_EASTERN = pytz.timezone("America/New_York")


def is_us_dst() -> bool:
    """현재 미국 동부시간이 DST(써머타임) 적용 중인지 확인"""
    now_et = datetime.now(US_EASTERN)
    return bool(now_et.dst().seconds > 0)


def get_us_briefing_time() -> tuple[int, int]:
    """
    미장 개장 1시간 전 브리핑 시각 (KST) 반환
    EDT(써머타임): 09:30 EDT = 22:30 KST → 브리핑 21:30
    EST(겨울):    09:30 EST = 23:30 KST → 브리핑 22:30
    """
    if is_us_dst():
        return 21, 30  # EDT
    else:
        return 22, 30  # EST


def get_us_close_time() -> tuple[int, int]:
    """
    미장 마감 시각 (KST) 반환
    EDT: 16:00 EDT = 05:00 KST
    EST: 16:00 EST = 06:00 KST
    """
    if is_us_dst():
        return 5, 0   # EDT
    else:
        return 6, 0   # EST


def get_market_status() -> dict:
    """현재 시장 상태 요약"""
    dst = is_us_dst()
    us_hour, us_min = get_us_briefing_time()
    us_close_h, us_close_m = get_us_close_time()
    return {
        "us_dst": dst,
        "us_briefing_kst": f"{us_hour:02d}:{us_min:02d}",
        "us_open_kst": "22:30" if dst else "23:30",
        "us_close_kst": f"{us_close_h:02d}:{us_close_m:02d}",
        "kr_briefing_kst": "07:00",
        "kr_open_kst": "08:00",
        "kr_close_kst": "20:30",
    }
