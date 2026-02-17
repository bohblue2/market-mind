# Domain Refactor Runbook

## 1) Current architecture snapshot
- Domain spiders are separated under `spiders/naver/` and `spiders/hankyung/`.
- Domain pipelines are separated under `pipelines/naver.py` and `pipelines/canonical.py`.
- Domain items are separated under `items/naver.py`, `items/hankyung.py`, and `items/canonical.py`.
- Domain middlewares are separated under `middlewares/naver.py`.
- Pipeline wiring is centralized in `scrapy_settings.py` with `DOMAIN_ITEM_PIPELINES`.

## 2) How pipeline composition works
- Base class `DomainPipelineSpider` in `spiders/base_domain_spider.py` builds effective `ITEM_PIPELINES` at spider settings priority.
- Each spider sets `pipeline_domain` (`naver`, `hankyung`, etc.).
- `DomainPipelineSpider.update_settings` reads:
  - `COMMON_ITEM_PIPELINES` (optional),
  - `DOMAIN_ITEM_PIPELINES` (required),
  - spider `custom_settings["ITEM_PIPELINES"]` (optional).
- Effective execution order still follows Scrapy priority numbers (smaller runs first).

## 3) Add a new domain
1. Create domain spider package under `spiders/<domain>/`.
2. Set `pipeline_domain = "<domain>"` in each spider class.
3. Add domain item modules under `items/<domain>.py` if needed.
4. Add domain pipeline module under `pipelines/<domain>.py`.
5. Register pipeline classes in `scrapy_settings.py` under `DOMAIN_ITEM_PIPELINES["<domain>"]`.
6. Add spider module path to `SPIDER_MODULES` if using a new package path.
7. Add middleware path in `DOWNLOADER_MIDDLEWARES` if domain-specific middleware is required.

## 4) Add a new spider in an existing domain
1. Place spider in existing package (for example `spiders/naver/`).
2. Inherit from `DomainPipelineSpider` or existing domain base spider.
3. Set `pipeline_domain` to existing domain key.
4. Keep spider `name` stable.
5. Only add spider-specific `custom_settings["ITEM_PIPELINES"]` when additional per-spider pipelines are needed.

## 5) Import conventions
- Use explicit domain item imports in spiders and pipelines:
  - `from mm_crawler.items.naver import ...`
  - `from mm_crawler.items.hankyung import ...`
  - `from mm_crawler.items.canonical import ...`
- Use explicit domain middleware path in settings:
  - `mm_crawler.middlewares.naver.NaverDelayMiddleware`

## 6) Guardrails
- Do not reintroduce monolith modules (`items.py`, `pipelines.py`, `middlewares.py`).
- Keep item field names aligned with ORM write paths in `pipelines/naver.py` and `pipelines/canonical.py`.
- Keep request metadata keys (`article_id`, `media_id`, `ticker`, `page`) unchanged unless pipeline code is updated together.
- Prefer minimal bugfix changes; avoid broad refactors during incident fixes.

## 7) Quick verification checklist
- `python3 -m compileall .`
- `python -m scrapy list` (if Scrapy installed in environment)
- Run one spider per domain as smoke test:
  - Naver example: `scrapy crawl naver_news_list -a ticker=005930 -a from_date=2024-01-01 -a to_date=2024-01-31`
  - Hankyung example: `scrapy crawl hankyung_consensus_list -a skin_type=market -a from_date=2024-01-01 -a to_date=2024-01-31`
