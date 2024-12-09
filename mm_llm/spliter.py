from typing import List, Sequence

import pymupdf
from langchain_core.documents import Document


def split_pdf(
    stream: bytearray | bytes, 
    report_id: str,
    batch_size: int = 1,
    save: bool = False
) -> List[bytes]:
    """Splits a PDF file into multiple smaller PDF files, each containing a specified number of pages.

    Args:
        filepath (str): The file path of the PDF file to be split.
        batch_size (int, optional): The number of pages each split PDF file should contain. Defaults to 10. The maximum value is 100.

    Returns:
        List[str]: A list of file paths for the newly created split PDF files.
    """
    input_pdf = pymupdf.open(stream=stream)
    len_pages = len(input_pdf)

    ret: List[bytes] = []
    
    for start_page in range(0, len_pages, batch_size):
        end_page = min(start_page + batch_size, len_pages) - 1
        
        output_filename = f"{report_id}_{start_page+1:04d}_{end_page+1:04d}.pdf"
        with pymupdf.open() as output_pdf:
            output_pdf.insert_pdf(input_pdf, from_page=start_page, to_page=end_page)
            if save:
                output_pdf.save(output_filename)
            ret.append(output_pdf.tobytes())
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
