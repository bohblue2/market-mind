from typing import List, Sequence

import pymupdf
from langchain_core.documents import Document


def split_pdf(filepath: str, batch_size: int=10) -> List[str]:
    input_pdf = pymupdf.open(filepath)
    len_pages = len(input_pdf)

    ret: List[str] = []
    
    for start_page in range(0, len_pages, batch_size):
        end_page = min(start_page + batch_size, len_pages) - 1
        
        input_file_basename = filepath.split('/')[-1].split('.')[0]
        output_filename = f"{input_file_basename}_{start_page+1:04d}_{end_page+1:04d}.pdf"
        with pymupdf.open() as output_pdf:
            output_pdf.insert_pdf(input_pdf, from_page=start_page, to_page=end_page)
            output_pdf.save(output_filename)
            ret.append(output_filename)

    input_pdf.close()
    return ret


def format_docs_with_page_break(docs: List[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def format_docs_with_ids(docs: Sequence[Document]) -> str:
    formatted_docs = []
    for i, doc in enumerate(docs):
        doc_string = f"<doc id='{i}'>{doc.page_content}</doc>"
        formatted_docs.append(doc_string)
    return "\n".join(formatted_docs)
