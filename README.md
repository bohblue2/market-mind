# Market Mind

<p align="center">
    <img src="./.github/assets/main.png" alt="Logo">
</p>

This project aims to develop algorithmic trading models that crawl news articles to predict and trade the direction of stocks and financial instruments.
It also aims to utilize the [LangChain-ai](https://github.com/langchain-ai) and [Transformers(HuggingFace)](https://github.com/huggingface/transformers)models to deeply analyze linguistic data from the financial domain and detect inefficiencies in the market.

For additional information, please refer to the [Team Notion](https://www.notion.so/yb98/097de26b8c5f4b5c83a4cd5b18c78103).

## Key Features

- **Analyze the causes of price fluctuations**: Infer the causes of price fluctuations in your holdings from analyst reports, electronic disclosures, and news data, and automatically report them.
- **Real-time data collection and ultra-short-term trading**: Collect analyst reports, electronic disclosures, and news data in real-time to execute ultra-short-term directional trading strategies.

This project aims to use advanced natural language processing (NLP) techniques to reduce information asymmetries in financial markets and maximize the performance of quantitative trading strategies.

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

```sql
'execute the following commands in the psql shell'
echo "CREATE EXTENSION vector;" | psql -U postgres -d market_mind
```
