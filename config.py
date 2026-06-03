import os
from dotenv import load_dotenv

# override=True: OS 환경변수가 비어 있어도 .env 값을 우선 적용 (env 가림 방지)
load_dotenv(override=True)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# RSS 피드 목록
RSS_FEEDS = {
    "한국증시": [
        "https://www.hankyung.com/feed/finance",
        "https://rss.etnews.com/Section901.xml",
        "https://www.mk.co.kr/rss/30000001/",
    ],
    "미국증시": [
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "https://rss.cnn.com/rss/money_markets.rss",
        "https://finance.yahoo.com/news/rssindex",
    ],
    "암호화폐": [
        "https://coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
    ],
}

# 속보 키워드 (이 단어가 포함된 뉴스는 즉시 발송)
BREAKING_KEYWORDS = [
    "급락", "폭락", "서킷브레이커", "긴급", "충격",
    "crash", "halt", "emergency", "plunge", "surge",
    "파산", "상장폐지", "금리 인상", "금리 인하",
]

# 발송 스케줄 (KST)
SCHEDULE_KST = {
    "korean_market_briefing": "08:00",   # 국장 개장 1시간 전
    "us_market_briefing": "22:30",       # 미장 개장 1시간 전
}
