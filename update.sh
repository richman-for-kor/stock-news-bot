#!/data/data/com.termux/files/usr/bin/bash
# 최신 코드 받아서 봇 재시작 (git 방식)
# 사용법: bash update.sh
cd "$(dirname "$(readlink -f "$0")")" || exit 1

echo "📥 최신 코드 받는 중..."
git fetch origin
git reset --hard origin/main      # .env·db는 .gitignore라 그대로 보존됨

echo "🔄 봇 재시작..."
bash stop.sh
sleep 1
bash start.sh
