# noteit widget — Google Play reviews

Все доступные отзывы приложения [noteit widget - by sendit](https://play.google.com/store/apps/details?id=me.bukovitz.noteit) (`me.bukovitz.noteit`) с метаинформацией, собранные через [google-play-scraper](https://github.com/JoMingyu/google-play-scraper).

- **Дашборд (GitHub Pages):** https://kroune.github.io/noteit-reviews/

## Структура

- `scrape.py` — парсер: перебирает локали × порядки сортировки × фильтры по оценке, дедупликация по `reviewId`, чекпоинты в `data/scrape_state.json`
- `build_site.py` — сборка статического сайта из сырых данных
- `data/reviews_raw.jsonl` — сырые отзывы (по одному JSON на строку) со всей метой: `reviewId`, `userName`, `userImage`, `content`, `score`, `thumbsUpCount`, `reviewCreatedVersion`, `at`, `replyContent`, `repliedAt`, локаль
- `docs/` — статический сайт для GitHub Pages (`index.html`, `data/reviews.json`, `data/meta.json`)

## Обновление данных

```bash
.venv/bin/python scrape.py       # докачает новые отзывы (инкрементально)
.venv/bin/python build_site.py   # пересоберёт docs/
```
