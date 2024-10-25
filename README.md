# LLM Trader-py
<p align="center">
    <img src="assets/main.png" alt="Logo">
</p>

This project aims to develop algorithmic trading models that crawl news articles to predict and trade the direction of stocks and financial instruments.
It also aims to utilize the [LangChain-ai](https://github.com/langchain-ai) and [Transformers(HuggingFace)](https://github.com/huggingface/transformers)models to deeply analyze linguistic data from the financial domain and detect inefficiencies in the market.

For additional information, please refer to the [한글 문서](assets/README_KO.md) and [Team Notion](https://www.notion.so/yb98/097de26b8c5f4b5c83a4cd5b18c78103).

## Key Features
- **Analyze the causes of price fluctuations**: Infer the causes of price fluctuations in your holdings from analyst reports, electronic disclosures, and news data, and automatically report them.
- **Real-time data collection and ultra-short-term trading**: Collect analyst reports, electronic disclosures, and news data in real-time to execute ultra-short-term directional trading strategies.

This project aims to use advanced natural language processing (NLP) techniques to reduce information asymmetries in financial markets and maximize the performance of quantitative trading strategies.

## Usage
```bash
poetry install
poetry shell

# 반드시 datasets/articles.db 를 먼저 생성해야함
alembic upgrade head

# database/model 수정시 alembic 업데이
alembic revision --autogenerate -m "message"

# TASK1: 네이버 뉴스 링크 리스트를 datasets/articles.db 에 저장
scrapy crawl naver_news_content

# TASK2: 저장된 네이버 뉴스 링크 리스트에서 하나씩 뉴스 본문 파싱
scrapy crawl naver_news_list
```

## Scrapy-extension
- [scrapy-fake-agent](https://github.com/alecxe/scrapy-fake-useragent)
- [scrapy-playwright](https://github.com/scrapy-plugins/scrapy-playwright)

## html compression algorithm

The crawled HTML code is stored as binary, compressed using the `lzma` algorithm. [Simple tests](https://chat.openai.com/share/a0a256b4-6e04-4920-8f4e-7b7285977476) showed that among `lz4`, `gzip`, `bz2`, and `lzma`, `lzma` had the best compression ratio. Compression time was not considered.