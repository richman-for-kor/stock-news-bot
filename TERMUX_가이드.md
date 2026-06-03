# 📱 Termux 설치·실행 가이드 (밍동의 부자되기 봇)

## 0. 준비
- F-Droid에서 **Termux** 설치 (Play스토어 버전 X)
- 24시간 자동 실행 원하면 **Termux:Boot** 도 설치

---

## 1. 최초 1회 설정

```bash
# 폰 저장소 접근 권한
termux-setup-storage

# 시스템 라이브러리 (lxml용)
pkg update -y
pkg install python libxml2 libxslt -y
```

## 2. 봇 폴더 가져오기
PC에서 폰 `Download` 폴더에 `news_bot` 폴더를 복사한 뒤:

```bash
cp -r ~/storage/downloads/news_bot ~/
cd ~/news_bot
```

> ⚠️ `.env` 파일(봇 토큰·Gemini 키)이 폴더 안에 같이 있는지 꼭 확인!

## 3. 파이썬 패키지 설치

```bash
pip install python-telegram-bot feedparser APScheduler python-dotenv pytz tzdata requests aiohttp beautifulsoup4 lxml deep-translator
```

> `tzdata` 빠지면 `ZoneInfoNotFoundError: Asia/Seoul` 오류가 납니다 (Termux엔 시간대 DB가 없음).

## 4. 실행

```bash
bash start.sh
```

- 로그 보기: `tail -f ~/news_bot/bot.log`
- 끄기: `bash ~/news_bot/stop.sh`

---

## 5. (선택) 폰 켜면 자동 실행

```bash
mkdir -p ~/.termux/boot
cp ~/news_bot/termux_boot_start.sh ~/.termux/boot/
```
Termux:Boot 앱을 한 번 열어두면, 이후 폰을 재부팅할 때마다 봇이 자동으로 켜집니다.

---

## 문제 해결
- **`bad interpreter` / `^M` 오류**: 윈도우 줄바꿈 때문. 한 번만 실행 →
  `sed -i 's/\r$//' start.sh stop.sh`
- **봇이 안 켜짐**: `python main.py` 직접 실행해서 오류 메시지 확인
- **`Conflict` 오류**: 봇이 두 개 떠 있는 것 → `bash stop.sh` 후 다시 `bash start.sh`
- **배터리 최적화**: 설정 → 배터리 → Termux → 제한 없음
