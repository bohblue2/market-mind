from typing import List

import pymupdf


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

    