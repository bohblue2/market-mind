# Market Mind

<p align="center">
    <img src="./.github/assets/main.png" alt="Logo">
</p>

This project aims to develop algorithmic trading models that crawl news articles to predict and trade the direction of stocks and financial instruments.
It also aims to utilize the [LangChain-ai](https://github.com/langchain-ai) and [Transformers(HuggingFace)](https://github.com/huggingface/transformers)models to deeply analyze linguistic data from the financial domain and detect inefficiencies in the market.

## Key Features

- **Analyze the causes of price fluctuations**: Infer the causes of price fluctuations in your holdings from analyst reports, electronic disclosures, and news data, and automatically report them.
- **Real-time data collection and ultra-short-term trading**: Collect analyst reports, electronic disclosures, and news data in real-time to execute ultra-short-term directional trading strategies.

This project aims to use advanced natural language processing (NLP) techniques to reduce information asymmetries in financial markets and maximize the performance of quantitative trading strategies.

## How to use
```bash
# scrapy the news articles *list* for the given date and ticker
make nl ticker=005930 from_date=2024-12-09 to_date=2024-12-10

# scrapy the news articles *list* for the given date and category
make nl_main target_date=2024-12-09
# or 
make nl_outlook target_date=2024-12-09

# scrapy the news articles *content* for the given date and category
make nc from_date=2024-12-08 to_date=2024-12-12 ticker=null category=main
# or
make nc from_date=2024-12-08 to_date=2024-12-12 ticker=null category=outlook

# ingest the news articles *content* for the given date and ticker
python cli.py mm-llm ingest-news --from-date 2024-12-09 --to-date 2024-12-11

# do the credit risk accessment for the given category
python cli.py mm-llm do-credit-risk-accessment --category=main
```

## Deployments

```bash
# set ENVIRONMENT variable to DEV/STAGE/PROD
export ENVIRONMENT=STAGE 
# set PYTHONPATH to the root directory (when dev environment)
export PYTHONPATH=$(pwd)

# Run the docker-compose file
docker-compose -f .dockerfiles/docker-compose.yml up -d

# Migrate db with the following command
# ALEMBCI_DB_URL is the database url in .dev.crawler.env/.prod.crawler.env file
export ALEMBIC_DB_URL=postgresql://postgres:postgres@127.0.0.1:5432/market_mind
# for stage environment
export ALEMBIC_DB_URL=postgresql://postgres:postgres@192.168.219.191:5432/market_mind
# Check the current revision
alembic current
# Upgrade the database
alembic upgrade head
# Create a new revision
alembic revision --autogenerate -m "init"
# Upgrade the database
alembic upgrade head
# check the current revision
alembic current

# Set-up redis server
docker exec -i -t mm-redis-standalone redis-cli -a "redis"  
# Check the redis server info
INFO
# Set the password for the user redis
ACL SETUSER redis on >redis
# Set the permission for the user redis
ACL SETUSER redis +@all
# Check the list of users
ACL LIST
```

## Deployments-postgresql

execute the following commands in the psql shell

```sql
echo "CREATE EXTENSION vector;" | psql -U postgres -d market_mind
```

## Dependencies-grit

```bash
$ openai migrate
Downloading Grit CLI from https://github.com/getgrit/gritql/releases/latest/download/marzano-x86_64-unknown-linux-gnu.tar.gz
Error: Failed to download Grit CLI from https://github.com/getgrit/gritql/releases/latest/download/marzano-x86_64-unknown-linux-gnu.tar.gz

$ curl -fsSL https://docs.grit.io/install | bash
downloading grit 0.1.0-alpha.1730315451 x86_64-unknown-linux-gnu
installing to /home/marcus/.grit/bin
  grit
everythings installed!

To add $HOME/.grit/bin to your PATH, either restart your shell or run:

    source $HOME/.grit/bin/env (sh, bash, zsh)
    source $HOME/.grit/bin/env.fish (fish)

$  source $HOME/.grit/bin/env 

$ grit apply openai
```

## Developement-scrapy

```bash
scrapy shell
```

```python
>>> fetch("https://finance.naver.com/news/mainnews.naver?date=2024-12-11")
>>> bs = response.css("#contentarea_left > div.mainNewsList._replaceNewsLink > ul").extract()
>>> from bs4 import BeautifulSoup
>>> soup = BeautifulSoup(bs[0], 'html.parser')
>>> articles = soup.find_all('li', class_='block1')
```

## Developement-postgresql

```sql
-- ENUM 타입 생성
CREATE TYPE naverarticlecategoryenum AS ENUM (
    'MAIN',
    'OUTLOOK',
    'ANALYSIS',
    'GLOBAL',
    'DERIVATIVES',
    'DISCLOSURES',
    'FOREX'
);

-- naver_article_list 테이블에 category 컬럼 추가
ALTER TABLE naver_article_list
ADD COLUMN category naverarticlecategoryenum;
```