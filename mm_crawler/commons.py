import os

import aiofiles
import httpx
import requests


def download_pdf(url: str, save_path: str) -> None:
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"PDF successfully downloaded and saved to {save_path}")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")


async def async_download_pdf(url, save_path):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(response.content)
            print(f"성공적으로 다운로드되어 {save_path}에 저장되었습니다.")
        else:
            print(f"다운로드에 실패했습니다. 상태 코드: {response.status_code}")

async def async_load_to_buffer(url: str, buffer: bytearray) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        
        if response.status_code == 200:
            buffer.extend(response.content)
            print("Buffer successfully loaded with data from the URL.")
        else:
            print(f"Failed to load buffer. Status code: {response.status_code}")
