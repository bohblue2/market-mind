.PHONY: b
b:
	@echo "Run backend"
	PYTHONPATH=$(pwd) python -m mm_backend

.PHONY: c1 
c1:
	@echo "Crawl naver_research_market_info"
	scrapy crawl naver_research_market_info -a from_date=2024-11-27 -a to_date=2024-11-29

.PHONY: c2 
c2:
	@echo "Crawl naver_news_content"
	scrapy crawl naver_news_content -a ticker=005930 -a from_date=2023-11-27 -a to_date=2024-12-04

.PHONY: c4
c4:
	@echo "Crawl naver_news_list"
	scrapy crawl naver_news_list -a ticker=005930 -a from_date=2023-11-27 -a to_date=2024-12-04