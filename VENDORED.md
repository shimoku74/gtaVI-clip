# Vendored plugin

`vendor/gtavi-claudecode/` — копия https://github.com/Bodila51/gtavi-claudecode
на коммите `67acdb4391fa491821b908bb7c455cf8148ad515` (2026-11-18), лицензия MIT.

Код прочитан целиком (13 скриптов + 16 скиллов): нет eval/exec, shell=True, чтения
паролей/ключей, скрытых хостов. Внешние обращения: Twitch (gql + анонимный IRC),
Kick, Reddit, YouTube (через yt-dlp), скачивание модели детекции лиц с opencv_zoo,
edge-tts и deep-translator (онлайн-сервисы).

Ставим именно эту копию, а не `Bodila51/...` напрямую: если автор позже изменит
код, у нас ничего не поменяется. Обновлять — только после повторного просмотра diff.
