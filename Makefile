# Set PYTHONPATH globally
PYTHONPATH := $(pwd)
ENVIRONMENT := STAGE

.PHONY: backend
backend:
	@echo "Run backend"
	python -m mm_backend

# ----------------------------

.PHONY: rmi
rmi:
	scrapy crawl naver_research_market_info \
		-a from_date=$(from_date) \
		-a to_date=$(to_date)

.PHONY: rcl 
rcl:
	scrapy crawl naver_research_company_list \
		-a from_date=$(from_date) \
		-a to_date=$(to_date)

.PHONY: rdl 
rdl:
	scrapy crawl naver_research_debenture_list \
		-a from_date=$(from_date) \
		-a to_date=$(to_date)

.PHONY: rel
rel:
	scrapy crawl naver_research_economy_list \
		-a from_date=$(from_date) \
		-a to_date=$(to_date)

.PHONY: ridl
ridl:
	scrapy crawl naver_research_industry_list \
		-a from_date=$(from_date) \
		-a to_date=$(to_date)

.PHONY: rivl
rivl:
	scrapy crawl naver_research_invest_list \
		-a from_date=$(from_date) \
		-a to_date=$(to_date)

# ----------------------------

.PHONY: nc
nc:
	scrapy crawl naver_news_content \
		-a from_date=$(from_date) \
		-a to_date=$(to_date) \
		-a ticker=$(ticker) \
		-a category=$(category)


.PHONY: nc_main
nc_main:
	scrapy crawl naver_news_content \
		-a from_date=$(from_date) \
		-a to_date=$(to_date) \
		-a ticker=null \
		-a category=main

.PHONY: nc_outlook
nc_outlook:
	scrapy crawl naver_news_content \
		-a from_date=$(from_date) \
		-a to_date=$(to_date) \
		-a ticker=null \
		-a category=outlook

.PHONY: nc_analysis
nc_analysis:
	scrapy crawl naver_news_content \
		-a from_date=$(from_date) \
		-a to_date=$(to_date) \
		-a ticker=null \
		-a category=analysis

.PHONY: nc_global
nc_global:
	scrapy crawl naver_news_content \
		-a from_date=$(from_date) \
		-a to_date=$(to_date) \
		-a ticker=null \
		-a category=global

.PHONY: nc_derivatives
nc_derivatives:
	scrapy crawl naver_news_content \
		-a from_date=$(from_date) \
		-a to_date=$(to_date) \
		-a ticker=null \
		-a category=derivatives

.PHONY: nc_disclosures
nc_disclosures:
	scrapy crawl naver_news_content \
		-a from_date=$(from_date) \
		-a to_date=$(to_date) \
		-a ticker=null \
		-a category=disclosures

.PHONY: nc_forex
nc_forex:
	scrapy crawl naver_news_content \
		-a from_date=$(from_date) \
		-a to_date=$(to_date) \
		-a ticker=null \
		-a category=forex

# ----------------------------

.PHONY: nl 
nl:
	scrapy crawl naver_news_list \
	-a ticker=$(ticker) \
	-a from_date=$(from_date) \
	-a to_date=$(to_date)

.PHONY: nl_main
nl_main:
	scrapy crawl naver_main_news_list \
		-a target_date=$(target_date)

.PHONY: nl_outlook
nl_outlook:
	scrapy crawl naver_outlook_news_article_list \
		-a target_date=$(target_date)

.PHONY: nl_analysis
nl_analysis:
	scrapy crawl naver_analysis_news_article_list \
		-a target_date=$(target_date)

.PHONY: nl_global
nl_global:
	scrapy crawl naver_global_news_article_list \
		-a target_date=$(target_date)

.PHONY: nl_derivatives
nl_derivatives:
	scrapy crawl naver_derivatives_news_article_list \
		-a target_date=$(target_date)

.PHONY: nl_disclosures
nl_disclosures:
	scrapy crawl naver_disclosures_news_article_list \
		-a target_date=$(target_date)

.PHONY: nl_forex
nl_forex:
	scrapy crawl naver_forex_news_article_list \
		-a target_date=$(target_date)