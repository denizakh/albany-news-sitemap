# Albany & Tree — News Sitemap через GitHub

Этот набор файлов автоматически генерирует `news-sitemap.xml` из основного `sitemap.xml` вашего сайта.

## Что уже проверено

- `https://albanyantree.com/robots.txt` существует и уже указывает на `sitemap.xml`.
- `https://albanyantree.com/news-sitemap.xml` сейчас возвращает 404 (файл отсутствует).

## Быстрый план внедрения

1. Создайте репозиторий на GitHub и загрузите туда эти файлы.
2. Включите GitHub Actions (workflow `Generate News Sitemap`).
3. Включите GitHub Pages (ветка `main` или `master`, root).
4. Проверьте, что URL вида `https://<your-user>.github.io/<repo>/news-sitemap.xml` открывается.
5. Проксируйте этот файл на ваш домен как `https://albanyantree.com/news-sitemap.xml`.
6. Добавьте строку в `robots.txt`:
   - `Sitemap: https://albanyantree.com/news-sitemap.xml`
7. Отправьте sitemap в Google Search Console.

---

## Вариант A (рекомендуется): Cloudflare Worker + GitHub Pages

Так вы получите правильный URL **на вашем домене** (`albanyantree.com/news-sitemap.xml`).

### 1) Что делает генератор

Скрипт `generate_news_sitemap.py`:
- читает `https://albanyantree.com/sitemap.xml`;
- берет только URL, подходящие под `NEWS_URL_PATTERNS` (по умолчанию `/insights/.+`);
- оставляет публикации только за последние 48 часов;
- подтягивает `<title>` каждой страницы;
- собирает валидный `news-sitemap.xml`.

### 2) Автообновление

Workflow `.github/workflows/news-sitemap.yml`:
- запускается каждый час и вручную;
- генерирует `news-sitemap.xml`;
- коммитит обновленный файл в репозиторий.

### 3) Проксирование на домен

Используйте `cloudflare-worker.js`:
- создайте Worker;
- задайте secret/variable `NEWS_SITEMAP_URL` со значением:
  - `https://<your-user>.github.io/<repo>/news-sitemap.xml`
- добавьте route:
  - `albanyantree.com/news-sitemap.xml`

После этого на вашем домене появится рабочий `news-sitemap.xml`.

---

## Вариант B: только GitHub Pages (без Cloudflare)

Можно отправить в Search Console URL GitHub Pages напрямую (`https://<your-user>.github.io/<repo>/news-sitemap.xml`).

Но лучше использовать Вариант A, чтобы sitemap жил на том же домене, что и сайт.

---

## Локальный запуск (проверка)

```bash
python3 generate_news_sitemap.py
```

Появится файл `news-sitemap.xml`.

---

## Настройки через переменные окружения

- `SITE_URL` — базовый URL сайта
- `SITEMAP_URL` — где лежит основной sitemap
- `PUBLICATION_NAME` — название издания
- `PUBLICATION_LANGUAGE` — язык (`en`, `ru`)
- `LOOKBACK_HOURS` — окно новостей (обычно `48`)
- `MAX_URLS` — максимум URL (до `1000`)
- `NEWS_URL_PATTERNS` — regex-список через запятую

Пример:

```bash
NEWS_URL_PATTERNS="/insights/.+,/commodity-market-news/.+" python3 generate_news_sitemap.py
```
