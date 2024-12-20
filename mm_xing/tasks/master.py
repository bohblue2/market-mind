import asyncio
from typing import Any, List, Optional

from httpx import Client, Response
from pydantic import BaseModel

from mm_xing.auth import get_access_token
from mm_xing.block import (o3101InBlock, o3101OutBlock, t1764InBlock,
                           t1764OutBlock, t8401InBlock, t8401OutBlock,
                           t8424InBlock, t8424OutBlock, t8425InBlock,
                           t8425OutBlock, t8426InBlock, t8426OutBlock,
                           t8436InBlock, t8436OutBlock, t9943InBlock,
                           t9943OutBlock, t9944InBlock, t9944OutBlock)
from mm_xing.config import settings
from mm_xing.constant import (O3101,
                              T1764,
                              T8401, T8424, T8425, T8426, T8436, T9943, T9943S,
                              T9943V, T9944, TR_CODE_TO_URL, XING_REST_URL)
from mm_xing.schemas import XingDataConfig, XingTrHeaders


def get_data_config(config_type: str, tr_code: str) -> Optional[XingDataConfig]:
    """Get data configuration for a given TR code and type.
    
    Args:
        config_type: Type of configuration ("code" or "ticker")
        tr_code: Trading request code
    
    Returns:
        XingDataConfig if found, None otherwise
    """
    configs = {
        "code": {
            T1764: XingDataConfig(
                path=TR_CODE_TO_URL[T1764],
                tr_code=T1764,
                inblock=t1764InBlock(gubun1="0"),
                cb_handler=SingleOutBlockHandler(t1764OutBlock),
            ),
            T8424: XingDataConfig(
                path=TR_CODE_TO_URL[T8424], 
                tr_code=T8424,
                inblock=t8424InBlock(gubun1="0"),
                cb_handler=SingleOutBlockHandler(t8424OutBlock),
            ),
            T8425: XingDataConfig(
                path=TR_CODE_TO_URL[T8425],
                tr_code=T8425, 
                inblock=t8425InBlock(dummy=""),
                cb_handler=SingleOutBlockHandler(t8425OutBlock),
            ),
        },
        "ticker": {
            T8436: XingDataConfig(
                path=TR_CODE_TO_URL[T8436],
                tr_code=T8436,
                inblock=t8436InBlock(gubun="0"),
                cb_handler=SingleOutBlockHandler(t8436OutBlock),
            ),
            T8401: XingDataConfig(
                path=TR_CODE_TO_URL[T8401],
                tr_code=T8401,
                inblock=t8401InBlock(dummy="0"),
                cb_handler=SingleOutBlockHandler(t8401OutBlock),
            ),
            T8426: XingDataConfig(
                path=TR_CODE_TO_URL[T8426],
                tr_code=T8426,
                inblock=t8426InBlock(dummy="0"),
                cb_handler=SingleOutBlockHandler(t8426OutBlock),
            ),
            T9943V: XingDataConfig(
                path=TR_CODE_TO_URL[T9943],
                tr_code=T9943,
                inblock=t9943InBlock(gubun="V"),
                cb_handler=SingleOutBlockHandler(t9943OutBlock),
            ),
            T9943S: XingDataConfig(
                path=TR_CODE_TO_URL[T9943],
                tr_code=T9943,
                inblock=t9943InBlock(gubun="S"),
                cb_handler=SingleOutBlockHandler(t9943OutBlock),
            ),
            T9943: XingDataConfig(
                path=TR_CODE_TO_URL[T9943],
                tr_code=T9943,
                inblock=t9943InBlock(gubun=""),
                cb_handler=SingleOutBlockHandler(t9943OutBlock),
            ),
            T9944: XingDataConfig(
                path=TR_CODE_TO_URL[T9944],
                tr_code=T9944,
                inblock=t9944InBlock(dummy="0"),
                cb_handler=SingleOutBlockHandler(t9944OutBlock),
            ),
            O3101: XingDataConfig(
                path=TR_CODE_TO_URL[O3101],
                tr_code=O3101,
                inblock=o3101InBlock(gubun="0"),
                cb_handler=SingleOutBlockHandler(o3101OutBlock)
            ),
        }
    }
    return configs.get(config_type, {}).get(tr_code, None)

class SingleOutBlockHandler:
    def __init__(self, outblock_cls: Any):
        self.outblock_cls = outblock_cls
        
    def __call__(self, response: Response, config: XingDataConfig) -> List[Optional[BaseModel]]:    
        """Process the API response and convert to a list of model instances.

        Args:
            response (Response): The HTTP response from the Xing API
            config (XingDataConfig): Configuration for the TR request
        Returns:
            List[Optional[BaseModel]]: A list of model instances parsed from the response data.
                Each item is an instance of the outblock class specified during handler initialization.
                For example, with t1764OutBlock:
                [
                    t1764OutBlock(rank=0, tradno='000', tradname='외국계회원사전체'),
                    t1764OutBlock(rank=1, tradno='086', tradname='BNK증권'),
                    ...
                ]

        Raises:
            KeyError: If response does not contain expected outblock data
            ValueError: If response indicates an error (e.g. {'rsp_cd': 'IGW00214', 'rsp_msg': 'TR CD는 필수 입니다.'})
        """
        try:
            data = response.json()[f"{config.tr_code}OutBlock"]
        except KeyError:
            raise KeyError(f"Response does not contain expected outblock data: {response.json()}")
        return [self.outblock_cls(**x) for x in data ]


def request_xing_api(
    client: Client,
    headers: XingTrHeaders,
    config: XingDataConfig
) -> List[Optional[BaseModel]]:
    return config.cb_handler(
        client.post(
            url=config.path,
            json={config.inblock.__class__.__name__: config.inblock.model_dump()},
            headers=headers.model_dump(by_alias=True),
        ),
        config=config
    )

async def fetch_market_data(
    client: Client,
    headers: XingTrHeaders,
    config: XingDataConfig,
    delay_sec: float = 1
) -> List[Optional[BaseModel]]:
    """Fetch market data for given configurations"""
    headers.update_tr_code(config.tr_code)
    result = request_xing_api(client, headers, config)
    await asyncio.sleep(delay_sec)
    return result


async def initialize_client() -> tuple[Client, XingTrHeaders]:
    """Initialize HTTP client and headers"""
    client = Client(verify=False, base_url=XING_REST_URL)
    access_token = get_access_token(
        client,
        app_key=settings.XING_APP_KEY,
        app_secret=settings.XING_APP_SECRET,
    )
    headers = XingTrHeaders.update_access_token(access_token)
    return client, headers