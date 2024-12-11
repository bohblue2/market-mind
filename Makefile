.PHONY: b
b:
	@echo "Run backend"
	PYTHONPATH=$(pwd) python -m mm_backend

.PHONY: r1
r1:
	scrapy crawl naver_research_market_info -a from_date=2024-11-27 -a to_date=2024-11-29

.PHONY: r2 
r2:
	scrapy crawl naver_research_company_list -a from_date=2024-11-27 -a to_date=2024-11-29

.PHONY: r3 
r3:
	scrapy crawl naver_research_debenture_list -a from_date=2024-11-27 -a to_date=2024-11-29

.PHONY: r4 
r4:
	scrapy crawl naver_research_economy_list -a from_date=2024-11-27 -a to_date=2024-11-29

.PHONY: r5
r5:
	scrapy crawl naver_research_industry_list -a from_date=2024-11-27 -a to_date=2024-11-29

.PHONY: r6
r6:
	scrapy crawl naver_research_invest_list -a from_date=2024-11-27 -a to_date=2024-11-29

.PHONY: ac
ac:
	@echo "Crawl naver_news_content"
	scrapy crawl naver_news_content -a ticker=005930 -a from_date=2023-12-04 -a to_date=2024-12-09

.PHONY: al 
al:
	@echo "Crawl naver_news_list"
	scrapy crawl naver_news_list -a ticker=005930 -a from_date=2023-12-04 -a to_date=2024-12-09

.PHONY: c5
c5:
	PYTHONPATH=/Users/baeyeongmin/Desktop/workspace/market_mind python mm_llm/ingestor/naver_research_report.py
