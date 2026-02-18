# SPIDERS KNOWLEDGE BASE

## OVERVIEW
Scrapy spider package for Naver news and research sources.

## STRUCTURE
```text
spiders/
├── base_domain_spider.py         # Domain pipeline composition base spider
├── naver/
│   ├── naver_news_list.py        # Code-specific finance news list crawl
│   ├── naver_news_content.py     # Article body fetch and parse
│   ├── naver_main_news_list.py   # Main/outlook/analysis section crawlers
│   └── naver_research_list.py    # Market/company/industry research crawlers
├── hankyung/
│   └── hankyung_consensus_list.py
└── commons.py                    # Report URL parsing helper
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add finance news list behavior | `naver/naver_news_list.py` | Emits `NaverArticleItem` or `NaverArticleListFailedItem` |
| Add article-body parsing | `naver/naver_news_content.py` | Uses XPath + BeautifulSoup cleanup |
| Add section-news crawl | `naver/naver_main_news_list.py` | Reuse `BaseNaverNewsSpider` / `BaseNaverSectionNewsSpider` |
| Add research source | `naver/naver_research_list.py` | Reuse `NaverResearchBase` + `parse_with_common_columns`/`parse_with_extra_columns` |
| Add Hankyung consensus behavior | `hankyung/hankyung_consensus_list.py` | Emits `HankyungConsensusItem` |
| Parse report URL components | `commons.py` | Returns `NaverReportItem` |

## CONVENTIONS
- Keep spider `name` stable; CLI scheduling depends on it.
- Prefer extending base classes over new standalone crawl flow.
- Keep request metadata keys consistent (`article_id`, `media_id`, `ticker`, `page`) because pipelines rely on them.
- Set `pipeline_domain` in each domain spider and let `DomainPipelineSpider` compose `ITEM_PIPELINES` from settings.
- Maintain KST-localized datetime parsing for all scraped timestamps.

## DomainPipelineSpider Pipeline Wiring
`DomainPipelineSpider` (in `spiders/base_domain_spider.py`) overrides Scrapy's `Spider.update_settings(cls, settings)` to compose `ITEM_PIPELINES` at spider initialization time.

Why this exists:
- Avoid duplicating `ITEM_PIPELINES` per spider; pipelines are registered once per domain in `scrapy_settings.py` (`DOMAIN_ITEM_PIPELINES`).
- Allow deterministic composition: common pipelines + domain pipelines + optional spider override.

How composition works:
- Reads `COMMON_ITEM_PIPELINES` and `DOMAIN_ITEM_PIPELINES` from settings.
- If the spider class defines `pipeline_domain = "naver"` (etc), selects `DOMAIN_ITEM_PIPELINES[pipeline_domain]`.
- If the spider's `custom_settings` contains `ITEM_PIPELINES`, those entries are merged last.
- Writes the merged dict back via `settings.set("ITEM_PIPELINES", merged, priority="spider")` so the spider gets its own pipeline configuration.

Gotchas:
- Project-level `ITEM_PIPELINES` is not merged automatically; use `COMMON_ITEM_PIPELINES` / `DOMAIN_ITEM_PIPELINES` / spider `custom_settings["ITEM_PIPELINES"]`.
- CLI `-s ITEM_PIPELINES=...` can still override this (higher precedence than spider settings).

## ANTI-PATTERNS
- Do not change item field names without synchronizing `pipelines/naver.py` or `pipelines/canonical.py` DB mapping.
- Do not convert fatal/non-fatal error enum behavior in `naver/naver_news_list.py` without validating downstream failure persistence.
- Do not drop `custom_settings` middleware/pipeline declarations when creating new spiders; defaults differ by spider family.
- Do not silently swallow missing content/title branches; existing TODOs mark known gaps and should be handled explicitly.
