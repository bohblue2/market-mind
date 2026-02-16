# SPIDERS KNOWLEDGE BASE

## OVERVIEW
Scrapy spider package for Naver news and research sources.

## STRUCTURE
```text
spiders/
├── naver_news_list.py        # Code-specific finance news list crawl
├── naver_news_content.py     # Article body fetch and parse
├── naver_main_news_list.py   # Main/outlook/analysis section crawlers
├── naver_research_list.py    # Market/company/industry research crawlers
└── commons.py                # Report URL parsing helper
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add finance news list behavior | `naver_news_list.py` | Emits `NaverArticleItem` or `NaverArticleListFailedItem` |
| Add article-body parsing | `naver_news_content.py` | Uses XPath + BeautifulSoup cleanup |
| Add section-news crawl | `naver_main_news_list.py` | Reuse `BaseNaverNewsSpider` / `BaseNaverSectionNewsSpider` |
| Add research source | `naver_research_list.py` | Reuse `NaverResearchBase` + `parse_with_common_columns`/`parse_with_extra_columns` |
| Parse report URL components | `commons.py` | Returns `NaverReportItem` |

## CONVENTIONS
- Keep spider `name` stable; CLI scheduling depends on it.
- Prefer extending base classes over new standalone crawl flow.
- Keep request metadata keys consistent (`article_id`, `media_id`, `ticker`, `page`) because pipelines rely on them.
- Maintain KST-localized datetime parsing for all scraped timestamps.

## ANTI-PATTERNS
- Do not change item field names without synchronizing `pipelines.py` DB mapping.
- Do not convert fatal/non-fatal error enum behavior in `naver_news_list.py` without validating downstream failure persistence.
- Do not drop `custom_settings` middleware/pipeline declarations when creating new spiders; defaults differ by spider family.
- Do not silently swallow missing content/title branches; existing TODOs mark known gaps and should be handled explicitly.
