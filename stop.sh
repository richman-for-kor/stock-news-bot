#!/data/data/com.termux/files/usr/bin/bash
# 밍동의 부자되기 봇 — 종료 스크립트
# 사용법: bash stop.sh

pkill -f "python main.py" 2>/dev/null
termux-wake-unlock 2>/dev/null
echo "🛑 봇을 종료했습니다."
