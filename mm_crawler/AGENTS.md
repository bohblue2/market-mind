# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-15 09:57:29 KST
**Commit:** 4bdb9b9
**Branch:** main

## OVERVIEW
Python Scrapy crawler package for Naver finance/news/research ingestion.
Runtime path is spider -> item -> pipeline -> SQLAlchemy ORM, with Alembic migrations for schema evolution.

## STRUCTURE
```text
mm_crawler/
├── spiders/           # Domain spiders + pipeline composition base
├── pipelines/         # Domain persistence pipelines
├── items/             # Domain item schemas
├── middlewares/       # Domain downloader middlewares
├── database/          # SQLAlchemy models + session bootstrap
├── alembic/           # Migration environment and revisions
├── scrapy_settings.py # Global Scrapy settings
└── config.py          # Env-driven DB settings
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add new crawler target | `spiders/naver/`, `spiders/hankyung/` | Prefer extending existing base spiders in `spiders/naver/naver_main_news_list.py` or `spiders/naver/naver_research_list.py` |
| Change crawl throttling/UA/retry | `scrapy_settings.py`, `middlewares/naver.py`, spider `custom_settings` | Settings are split global + per-spider |
| Change item payload schema | `items/naver.py`, `items/hankyung.py`, `items/canonical.py` | Keep keys aligned with pipeline/model mapping |
| Change DB writes | `pipelines/naver.py`, `pipelines/canonical.py` | Pipelines own DB persistence and LZMA compression for article HTML |
| Change DB schema | `database/models.py`, `alembic/versions/` | Update model and add Alembic revision together |
| Change DB connection/env loading | `config.py`, `database/session.py`, `alembic/env.py` | Runtime and migration env loading are separate |

## CODE MAP
| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| `DomainPipelineSpider` | base spider | `spiders/base_domain_spider.py` | high | Composes domain pipelines from settings |
| `NaverNewsArticleList` | spider | `spiders/naver/naver_news_list.py` | high | Stock-code news list crawl |
| `NaverNewsArticleContents` | spider | `spiders/naver/naver_news_content.py` | high | Fetch and parse article body |
| `BaseNaverNewsSpider` | base spider | `spiders/naver/naver_main_news_list.py` | medium | Shared paging/header flow for section spiders |
| `NaverResearchBase` | base spider | `spiders/naver/naver_research_list.py` | high | Shared research-list crawl flow |
| `FinanceNewsListPipeline` | pipeline | `pipelines/naver.py` | high | Persist list/failure items |
| `FinanceNewsContentPipeline` | pipeline | `pipelines/naver.py` | high | Persist article content and scrape status |
| `ResearchMarketinfoListPipeline` | pipeline | `pipelines/naver.py` | high | Persist research reports and binary file |
| `CanonicalDocumentPipeline` | pipeline | `pipelines/canonical.py` | high | Persist canonical document streams |
| `SessionLocal` | DB session factory | `database/session.py` | high | Shared SQLAlchemy session maker |

## CONVENTIONS
- Scrapy settings file is `scrapy_settings.py` (not the common `settings.py`).
- Spider-specific `custom_settings` is used for downloader controls; pipelines are composed via `DomainPipelineSpider.update_settings` + `DOMAIN_ITEM_PIPELINES`.
- Timezone handling is explicit with KST localization (`Asia/Seoul`) in spiders/pipelines.
- Article content HTML is compressed with `lzma` before DB write.

## ANTI-PATTERNS (THIS PROJECT)
- Do not assume imports are side-effect free in `database/session.py`; it runs `init_db()` on import.
- Do not rely on test commands in this package; no test suite/config exists in this directory.
- Do not omit `ALEMBIC_DB_URL` when running migrations; `alembic/env.py` raises immediately.
- Deprecated-default note exists in `scrapy_settings.py` (`REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"`); keep compatibility when touching settings.

## UNIQUE STYLES
- Mixed async/sync style: async spider methods coexist with sync DB session operations.
- Spider names are mixed explicit/dynamic (`name = os.path.basename(__file__).replace('.py', '')` in several files).
- Parser logic uses BeautifulSoup and XPath in parallel depending on source page shape.

## COMMANDS
```bash
# Run a spider (examples)
scrapy crawl naver_news_list -a ticker=005930 -a from_date=2024-01-01 -a to_date=2024-01-31
scrapy crawl naver_news_content -a from_date=2024-01-01 -a to_date=2024-01-31 -a ticker=005930 -a category=code
scrapy crawl naver_research_market_info -a from_date=2024-01-01 -a to_date=2024-01-31

# Alembic migration workflow
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

## NOTES
- `config.py` chooses env file by `ENVIRONMENT` (`.env.dev.crawler`, `.env.stage.crawler`, `.env.prod.crawler`, fallback `.env.crawler`).
- `alembic/env.py` loads `.dev.crawler.env` then `.prod.crawler.env`; this differs from runtime `config.py` env naming.
- TODO markers exist in spiders; unfinished error-handling branches are expected in current codebase state.
