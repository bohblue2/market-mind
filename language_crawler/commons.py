import os
import requests

def download_pdf(url, save_path):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Ensure the save_path directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Write the content to a file
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"PDF successfully downloaded and saved to {save_path}")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")

import httpx

async def async_download_pdf(url, save_path):
    # 비동기 HTTP 클라이언트 생성
    async with httpx.AsyncClient() as client:
        # 비동기로 GET 요청 보내기
        response = await client.get(url)
    
        # 요청이 성공적인지 확인
        if response.status_code == 200:
            # save_path 디렉토리가 존재하는지 확인
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
            # 파일에 내용 쓰기
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"PDF가 성공적으로 다운로드되어 {save_path}에 저장되었습니다.")
        else:
            print(f"PDF 다운로드에 실패했습니다. 상태 코드: {response.status_code}")