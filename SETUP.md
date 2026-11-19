# Установка на твоём компьютере

Запускать нужно **локально**: YouTube блокирует IP облачных серверов
(«Sign in to confirm you're not a bot»), а на домашнем IP всё работает.
Я проверил: `stream-finder` (Twitch/Kick) и `campaign-finder` работают, `trend-radar` и
скачивание видео в облаке упираются в эту блокировку.

## 1. Инструменты
- **Python 3.10+** и **Claude Code** (CLI или приложение).
- **ffmpeg**:
  - Windows: `winget install --id Gyan.FFmpeg -e --source winget`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install -y ffmpeg`

## 2. Репозиторий
```
git clone <URL этого репозитория>
cd gta6-clip-desk
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r vendor/gtavi-claudecode/requirements.txt
```

## 3. Плагин в Claude Code (проверенная копия, не из интернета)
Открой Claude Code в папке репозитория:
```
/plugin marketplace add ./vendor/gtavi-claudecode
/plugin install gtavi-claudecode@gtavi-claudecode
```

## 4. Первый запуск
Вставь в Claude Code:
```
Use gtavi-claudecode. Set up my GTA 6 clip page, ask me your 4 questions in one message,
then do everything after one "yes": find live clipping campaigns, show today's trending
GTA 6 videos and live streams, find the best moments in the top one, cut my first 3 clips
with hooks and credits, check them against the campaign rules, and tell me what to post where.
```

## 5. Если YouTube просит войти
Это значит, что YouTube заподозрил бота. Добавь в команды yt-dlp
`--cookies-from-browser chrome` (куки только твоего браузера, никому не отправляй).

## Безопасность
- Не давай плагину пароли и карты. Ему они не нужны.
- Публикуй только то, что разрешает кампания. Ничего «слитого» и «раннего».
- Обновлять `vendor/` только после просмотра diff (см. `VENDORED.md`).
