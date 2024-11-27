import os

import dotenv

from mm_xing.block import t9943InBlock

dotenv.load_dotenv('.dev.env')

XING_AUTH_URL = "oauth2/token"

XING_REST_URL = "https://openapi.ls-sec.co.kr:8080"
XING_APP_KEY:str | None = os.getenv("XING_APP_KEY") 
XING_APP_SECRET:str | None = os.getenv("XING_APP_SECRET")

MM_DB_PATH = "data"
SUBSCRIBE = "3"

T1764 = "t1764"
T8424 = "t8424"
T8425 = "t8425"
T8436 = "t8436"
T8401 = "t8401"
T8426 = "t8426"
T9943V = "t9943V"
T9943S = "t9943S"
T9943 = "t9943"
T9944 = "t9944"
O3101 = "o3101"

CODE = 'code'
TICKER = 'ticker'

TR_CODE_TO_TYPE = {
    T1764: CODE,
    T8424: CODE,
    T8425: CODE,
    T8436: TICKER,
    T8401: TICKER,
    T8426: TICKER,
    T9943: TICKER,
    T9943V: TICKER,
    T9943S: TICKER,
    T9944: TICKER,
    O3101: TICKER,
}

STOCK_EXCHANGE_PATH = "/stock/exchange"
INDTP_MARKET_DATA_PATH = "/indtp/market-data"
STOCK_SECTOR_PATH = "/stock/sector"

STOCK_ETC_PATH = "/stock/etc"
FUTUREOPTION_MARKET_DATA_PATH = "/futureoption/market-data" 
OVERSEAS_FUTUREOPTION_MARKET_DATA_PATH = "/overseas-futureoption/market-data"

TR_CODE_TO_URL = {
    T1764: STOCK_EXCHANGE_PATH,
    T8424: INDTP_MARKET_DATA_PATH,
    T8425: STOCK_SECTOR_PATH,
    T8436: STOCK_ETC_PATH,
    T8401: FUTUREOPTION_MARKET_DATA_PATH,
    T8426: FUTUREOPTION_MARKET_DATA_PATH,
    T9943: FUTUREOPTION_MARKET_DATA_PATH,
    T9944: FUTUREOPTION_MARKET_DATA_PATH,
    O3101: OVERSEAS_FUTUREOPTION_MARKET_DATA_PATH,
}

from mm_xing.block import (o3101InBlock, o3101OutBlock,  # noqa: E402
                           t1764InBlock, t1764OutBlock, t8401InBlock,
                           t8401OutBlock, t8424InBlock, t8424OutBlock,
                           t8425InBlock, t8425OutBlock, t8426InBlock,
                           t8426OutBlock, t8436InBlock, t8436OutBlock,
                           t9943InBlock, t9943OutBlock, t9944InBlock,
                           t9944OutBlock)

TR_CODE_TO_BLOCK = {
    T8436: (t8436InBlock(gubun="0"), t8436OutBlock),
    T8401: (t8401InBlock(dummy="0"), t8401OutBlock),
    T8426: (t8426InBlock(dummy="0"), t8426OutBlock),
    T9943: (t9943InBlock(gubun=""), t9943OutBlock),
    T9944: (t9944InBlock(dummy="0"), t9944OutBlock),
    O3101: (o3101InBlock(gubun="0"), o3101OutBlock),
}
