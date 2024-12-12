import os

import click

@click.group()
def cli():
    """Main CLI group."""
    pass

@cli.group()
def mm_xing(): ...

@mm_xing.command()
@click.argument('task', type=click.Choice(['create_pydantic_model', 'create_msgspec_model_for_websocket']))
@click.option('--path', default='./res', help='The default xing api res file path.')
def res_converter(task, path):
    """Perform tasks related to res conversion."""
    from mm_xing.res_converter import (create_msgspec_model_for_websocket,
                                       create_pydantic_model,
                                       create_res_file_mapping, parse_res)

    res_file_paths = [
        os.path.join(path, file_name)
        for file_name in os.listdir(path)
        if os.path.isfile(os.path.join(path, file_name)) and "_" not in file_name
    ]
    res_rows = [parse_res(path) for path in res_file_paths]
    res_map = create_res_file_mapping(res_rows)

    res_code = sorted(res_map.keys())
    res_infos = [res_map[name] for name in res_code]

    if task == "create_pydantic_model":
        create_pydantic_model(res_infos=res_infos)
    elif task == "create_msgspec_model_for_websocket":
        create_msgspec_model_for_websocket(res_infos=res_infos)

@cli.group()
def mm_llm(): ...

@mm_llm.command()
@click.option('--ticker', default=None, help='Ticker symbol, e.g., 삼성전자, 005930')
@click.option('--from-date', required=True, help='Start date for news ingestion, e.g., 2024-12-07')
@click.option('--to-date', required=True, help='End date for news ingestion, e.g., 2024-12-10')
@click.option('--chunk-size', default=1500, help='Chunk size for news ingestion')
@click.option('--chunk-overlap', default=150, help='Chunk overlap for news ingestion')
@click.option('--yield-size', default=1000, help='Yield size for news ingestion')
@click.option('--is-upsert', is_flag=True, default=False, help='Flag to upsert news articles')
def ingest_news(ticker, from_date, to_date, chunk_size, chunk_overlap, yield_size, is_upsert):
    """Ingest news articles from Naver News."""
    from mm_llm.ingestor.naver_news_article import NaverNewsIngestor
    ingestor = NaverNewsIngestor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    ingestor.ingest_news_articles(
        ticker=ticker,
        from_datetime=from_date,
        to_datetime=to_date,
        yield_size=yield_size,
        is_upsert=is_upsert
    )
    print(f"Successfully processed news articles for ticker {ticker}")

@mm_llm.command()
@click.option('--yield-size', default=1000, help='Number of records to yield per batch')
@click.option('--commit-size', default=10, help='Number of records to commit per transaction')
@click.option('--from-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date for report ingestion, e.g., 2024-12-07')
@click.option('--to-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='End date for report ingestion, e.g., 2024-12-10')
@click.option('--is-upsert', is_flag=True, default=False, help='Flag to upsert research reports')
def ingest_reports(yield_size, commit_size, from_date, to_date, is_upsert):
    """Ingest research reports from Naver."""
    from mm_llm.ingestor.naver_research_report import NaverResearchReportIngestor
    ingestor = NaverResearchReportIngestor(
        yield_size=yield_size,
        commit_size=commit_size
    )
    ingestor.ingest_research_reports(
        from_dt=from_date,
        to_dt=to_date,
        is_upsert=is_upsert
    )
    print("Successfully processed research reports")


@mm_llm.command()
@click.option('--entity-type', type=click.Choice(['article', 'report']), required=True, help='Type of entity to process: article or report')
@click.option('--is-upsert', is_flag=True, default=False, help='Flag to upsert chunks into the vector store')
def process_chunks(entity_type, is_upsert):
    """Process chunks for articles or reports and store them in a vector store."""
    from mm_llm.ingestor.pg_chunk import pg_process_chunks
    from mm_crawler.database.models import NaverArticleChunkOrm, NaverResearchReportChunkOrm
    from mm_llm.pg_retriever import init_vector_store

    if entity_type == 'article':
        vector_store = init_vector_store("naver_news_articles")
        pg_process_chunks(
            NaverArticleChunkOrm,
            vector_store,
            metadata_mapping={"article_id": "article_id", "chunk_num": "chunk_num"},
            is_upsert=is_upsert
        )
        print("Successfully processed article chunks")
    elif entity_type == 'report':
        vector_store = init_vector_store("naver_research_reports")
        pg_process_chunks(
            NaverResearchReportChunkOrm,
            vector_store,
            metadata_mapping={"report_id": "report_id", "chunk_num": "chunk_num"},
            is_upsert=is_upsert
        )
        print("Successfully processed report chunks")

if __name__ == "__main__":
    cli()