import json
import os
from typing import Any, List, Optional
import asyncio

from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel
import requests
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import joinedload

from mm_crawler.database.models import (NaverResearchReportFileOrm)
from mm_crawler.database.session import SessionLocal
from mm_llm.commons import report_id_formatter
from mm_llm.config import settings
from mm_llm.ingestor.commons import process_chunk
from mm_llm.spliter import split_pdf
from requests.models import Response
import tempfile

from mm_llm.vectorstore.milvus import get_milvus_client, get_naver_research_report_collection

class ReportPage(BaseModel):
    report_id: int
    content_html: str
    page_num: int


from diskcache import FanoutCache
cache_splited_pages = FanoutCache(
    directory=".cache/naver_report_splited_pages",
    timeout=1,
    shards=64,
    size_limit=4e9,
    eviction_policy="least-recently-used",
) # key: {report_id}_{page_num} value: bytes
cache_splited_pages.stats(enable=True)
cache_upstage_response = FanoutCache(
    directory=".cache/naver_report_upstage_response",
    timeout=1,
    shards=64,
    size_limit=4e9,
    eviction_policy="least-recently-used",
) # key: {report_id}_{page_num} value: json
cache_upstage_response.stats(enable=True)

def upstage_layout_analysis(report_id: str):
    input_stream: Optional[bytes] = cache_splited_pages.get(report_id)      # type: ignore
    response: Optional[Response] = cache_upstage_response.get(report_id)    # type: ignore

    if input_stream is None:
        raise ValueError(f"Unexpected report_id {report_id} for input_stream.")
    if response is None:
        response = requests.post(
            "https://api.upstage.ai/v1/document-ai/document-parse",
            headers={"Authorization": f"Bearer {settings.UPSTAGE_API_KEY}"},
            data={"ocr": False},
            files={"document": input_stream}
        )
        cache_upstage_response.set(report_id, response)
        
        # Create temporary directory and save response
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, f"{report_id}_upstage.json")
            if response.status_code == 200:
                with open(output_file, "w") as f:
                    json.dump(response.json(), f, ensure_ascii=False)
            else:
                raise ValueError(f"Unexpected status code {response.status_code}.")
        response.encoding = 'utf-8'
    return response
    

def process_research_report(report: NaverResearchReportFileOrm) -> List[ReportPage]:
    pages = []    
    bytes_buffer: bytearray = report.file_data  # type: ignore
    report_id: int = report.report_id           # type: ignore
    pdf_pages: List[bytes] = split_pdf(
        bytes_buffer, 
        report_id_formatter(report_id), 
        batch_size=1
    ) # type: ignore

    for page_num, page in enumerate(pdf_pages):
        report_id_key = f"{report_id_formatter(report_id)}_{page_num}"
        cache_splited_pages.set(report_id_key, page)
        response = upstage_layout_analysis(report_id=report_id_key)

        if response.status_code == 200:
            response_json = response.json()
            content_html = response_json.get("content", {}).get("html", "")
            pages.append(ReportPage(
                    report_id=report_id,
                    content_html=content_html,
                    page_num=page_num
            ))
        else:
            raise ValueError(f"Unexpected status code {response.status_code}.")
    return pages

async def main() -> None:
    sess: Session = SessionLocal() 
    yield_size = 1000
    vec_client = get_milvus_client(uri=settings.MILVUS_URI)
    collection = get_naver_research_report_collection()
    VEC_COLLECTION_FLUSH_SIZE = 10
    
    collection_rows = []
    for report_file in sess.query(
        NaverResearchReportFileOrm
    ).options(
        joinedload(NaverResearchReportFileOrm.naver_research_report)
    ).yield_per(yield_size).all():
        report = report_file.naver_research_report
        pages = process_research_report(report_file)

        enhanced_chunks: list[str] = []
        enhanced_embeddings: list[Any] = []
        whole_document = report.title
        whole_document += " ".join(page.content_html for page in pages)
        tasks = [
            process_chunk(
                whole_document=whole_document,
                chunk_content=page.content_html
            )
            for page in pages
        ]
        results = await asyncio.gather(*tasks)
        enhanced_chunks, enhanced_embeddings = map(list, zip(*results))
        enhanced_chunks = list(enhanced_chunks)
        enhanced_embeddings = list(enhanced_embeddings)

        for chunk_num, (content, content_embedding) in enumerate(zip(enhanced_chunks, enhanced_embeddings)):
            collection_rows.append(
                dict(
                    report_id=report.report_id,
                    chunk_num=chunk_num,
                    title=report.title,
                    issuer_company_name=report.issuer_company_name,
                    issuer_company_id=report.issuer_company_id,
                    report_category=report.report_category,
                    target_company=report.target_company or "",
                    target_industry=report.target_industry or "",
                    content=content,
                    content_embedding=content_embedding,  # Assuming embeddings are generated later
                    tags=[],  # Assuming tags are generated or provided elsewhere
                    date=int(report.date.timestamp()),
                    updated_at=int(report.updated_at.timestamp()),
                    created_at=int(report.created_at.timestamp())
                )
            )
        if len(collection_rows) >= VEC_COLLECTION_FLUSH_SIZE:
            print(f"Upserting {len(collection_rows)} documents to Milvus collection {collection.name}.")
            vec_client.upsert(
                collection_name=collection.name,
                data=collection_rows,
            )
            collection_rows.clear()
        
    if collection_rows:
        print(f"[Finishing] Upserting {len(collection_rows)} documents to Milvus collection {collection.name}.")
        vec_client.upsert(
            collection_name=collection.name,
            data=collection_rows,
        )
        collection_rows.clear()
    
    hits, misses = cache_upstage_response.stats(enable=False, reset=True)
    print(f"hits: {hits}, misses: {misses}")
    sess.close()
    

if __name__ == "__main__":
    asyncio.run(main())