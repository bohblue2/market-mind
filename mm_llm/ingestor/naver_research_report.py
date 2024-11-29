import json
from typing import List

import requests
from sqlalchemy import LargeBinary, Result
from sqlalchemy.orm.session import Session

from mm_crawler.database.models import (NaverArticleContentOrm,
                                        NaverResearchReportFileOrm)
from mm_crawler.database.session import SessionLocal
from mm_llm.commons import report_id_formatter
from mm_llm.config import settings
from mm_llm.spliter import split_pdf


def upstage_layout_analysis(input_stream: bytes, report_id: str):
    response = requests.post(
        "https://api.upstage.ai/v1/document-ai/document-parse",
        headers={"Authorization": f"Bearer {settings.UPSTAGE_API_KEY}"},
        data={"ocr": False},
        files={"document": input_stream}
    )
    # Save response
    output_file = f"{report_id}_upstage.json"
    if response.status_code == 200:
        with open(output_file, "w") as f:
            json.dump(response.json(), f, ensure_ascii=False)
    else:
        raise ValueError(f"Unexpected status code {response.status_code}.")
    
    

def ingest_research_report_to_milvus(sess: Session):
    report_pdf_files: List[NaverResearchReportFileOrm] = sess.query(NaverResearchReportFileOrm).yield_per(10).all() # type: ignore
    
    for report in report_pdf_files: # type ignore
        bytes_buffer: bytearray = report.file_data # type: ignore
        report_id: int = report.report_id # type: ignore
        ret = split_pdf(bytes_buffer, report_id_formatter(report_id), batch_size =1) # type: ignore

if __name__ == "__main__":
    sess = SessionLocal()
    ingest_research_report_to_milvus(sess)
