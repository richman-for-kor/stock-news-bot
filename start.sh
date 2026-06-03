#!/data/data/com.termux/files/usr/bin/bash
# 밍동의 부자되기 봇 — Termux 실행 스크립트
# 사용법: bash start.sh

# 스크립트가 있는 폴더로 이동 (어디서 실행하든 동작)
cd "$(dirname "$(readlink -f "$0")")" || exit 1

# 1) 중복 실행 방지 — 기존 봇이 떠 있으면 종료 (텔레그램 Conflict 오류 예방)
pkill -f "python main.py" 2>/dev/null
sleep 2

# 2) 절전 방지 — 화면 꺼져도 CPU 유지 (Termux 기본 명령, 추가 설치 불필요)
termux-wake-lock

# 3) 백그라운드 실행 + 로그 기록
nohup python main.py > bot.log 2>&1 &

echo "✅ 봇 시작됨 (PID $!)"
echo "   📜 로그 보기 : tail -f $(pwd)/bot.log"
echo "   🛑 끄기      : bash $(pwd)/stop.sh"
