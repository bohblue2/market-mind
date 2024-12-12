import json
import os
import tempfile
from datetime import datetime
from typing import List, Optional

import requests
from diskcache import FanoutCache
from pydantic import BaseModel
from requests.models import Response
from sqlalchemy.orm import joinedload

from mm_crawler.database.models import (NaverResearchReportChunkOrm,
                                        NaverResearchReportFileOrm,
                                        NaverResearchReportOrm)
from mm_crawler.database.session import SessionLocal
from mm_llm.commons import report_id_formatter
from mm_llm.config import settings
from mm_llm.constant import KST
from mm_llm.ingestor.commons import process_chunk
from mm_llm.spliter import split_pdf


class ReportPage(BaseModel):
    report_id: int
    content_html: str
    page_num: int


class NaverResearchReportIngestor:
    def __init__(
        self, 
        yield_size: int | None = 1000, 
        commit_size: int | None = None,
        *, 
        sess=None
    ):
        self._yield_size = yield_size
        self._commit_size = commit_size
        self._sess = SessionLocal() if sess is None else sess
        
        # Initialize caches
        self.cache_splited_pages = FanoutCache(
            directory=".cache/naver_report_splited_pages",
            timeout=1,
            shards=64,
            size_limit=4e9,
            eviction_policy="least-recently-used",
        )
        self.cache_upstage_response = FanoutCache(
            directory=".cache/naver_report_upstage_response",
            timeout=1,
            shards=64,
            size_limit=4e9,
            eviction_policy="least-recently-used",
        )
        self.cache_splited_pages.stats(enable=True)
        self.cache_upstage_response.stats(enable=True)

    def _upstage_layout_analysis(self, report_id: str) -> Response:
        input_stream: Optional[bytes] = self.cache_splited_pages.get(report_id)     # type: ignore
        response: Optional[Response] = self.cache_upstage_response.get(report_id)   # type: ignore

        if input_stream is None:
            raise ValueError(f"Unexpected report_id {report_id} for input_stream.")
        
        if response is None:
            response = requests.post(
                "https://api.upstage.ai/v1/document-ai/document-parse",
                headers={"Authorization": f"Bearer {settings.UPSTAGE_API_KEY}"},
                data={"ocr": False},
                files={"document": input_stream}
            )
            self.cache_upstage_response.set(report_id, response)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = os.path.join(temp_dir, f"{report_id}_upstage.json")
                if response.status_code == 200:
                    with open(output_file, "w") as f:
                        json.dump(response.json(), f, ensure_ascii=False)
                else:
                    raise ValueError(f"Unexpected status code {response.status_code}.")
            response.encoding = 'utf-8'
        return response

    def _process_research_report(self, report: NaverResearchReportFileOrm) -> List[ReportPage]:
        pages = []    
        bytes_buffer: bytearray = report.file_data  # type: ignore
        report_id: int = report.report_id           # type: ignore
        pdf_pages: List[bytes] = split_pdf(
            bytes_buffer, 
            report_id_formatter(report_id), 
            batch_size=1
        )

        for page_num, page in enumerate(pdf_pages):
            report_id_key = f"{report_id_formatter(report_id)}_{page_num}"
            self.cache_splited_pages.set(report_id_key, page)
            response = self._upstage_layout_analysis(report_id=report_id_key)

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

    def ingest_research_reports(
        self, 
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        yield_size: int | None = None,
        commit_size: int | None = None,
        is_upsert: bool = False,
    ) -> None:
        yield_size = self._yield_size if self._yield_size is None else yield_size 
        commit_size = self._commit_size if self._commit_size is not None else commit_size 
        
        try:
            report_files = (
                self._sess.query(NaverResearchReportFileOrm)
                .join(NaverResearchReportOrm)
                .outerjoin(NaverResearchReportChunkOrm)
                .filter(
                    *([] if from_dt is None or to_dt is None else [NaverResearchReportOrm.published_at.between(from_dt, to_dt)]),
                    # Filter for chunks that either don't exist or match embedded_at condition
                    (
                        ~NaverResearchReportOrm.chunks.any() |  # No chunks exist
                        (
                            NaverResearchReportChunkOrm.embedded_at.is_(None) if not is_upsert
                            else NaverResearchReportChunkOrm.embedded_at.isnot(None)
                        )
                    )
                )
                .options(joinedload(NaverResearchReportFileOrm.naver_research_report))
                .yield_per(yield_size) # type: ignore
                .all()
            )
            for report_file in report_files: 
                report: NaverResearchReportOrm = report_file.naver_research_report
                pages = self._process_research_report(report_file)

                whole_document = report.title + " " + report.issuer_company_name 
                whole_document += " ".join(page.content_html for page in pages)
                processed_chunks = process_chunk(
                    whole_document=whole_document, # type: ignore
                    chunk_contents=[page.content_html for page in pages]
                )
                # process: 1. whole_document
                whole_chunks = "\n".join(processed_chunks.enhanced_chunks)
                whole_chunk_orm = NaverResearchReportChunkOrm(
                    report_id=report.report_id,
                    chunk_num=-1,
                    content=whole_chunks,
                    tags=[]
                )
                report.chunks.append(whole_chunk_orm)
                
                # process: 2. chunks
                for idx, content in enumerate(processed_chunks.enhanced_chunks):
                    chunk_orm = NaverResearchReportChunkOrm(
                        report_id=report.report_id,
                        chunk_num=idx,
                        content=content,
                        tags=[],   
                    )
                    report.chunks.append(chunk_orm)
                report.chunked_at = datetime.now(tz=KST) # type: ignore
                    
                if idx % commit_size == 0: # type: ignore
                    self._sess.commit()
            self._sess.commit()
        except Exception as e:
            self._sess.rollback()
            raise e
        finally:
            self._sess.close()

