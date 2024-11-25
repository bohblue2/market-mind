from datetime import datetime
from typing import Dict, List, Optional, Type, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from mm_backend.database.models import (RountineTaskOrm, o3101OutBlockOrm,
                                        t1764OutBlockOrm, t8401OutBlockOrm,
                                        t8424OutBlockOrm, t8425OutBlockOrm,
                                        t8426OutBlockOrm, t8436OutBlockOrm,
                                        t9943OutBlockOrm, t9943SOutBlockOrm,
                                        t9943VOutBlockOrm, t9944OutBlockOrm)
from mm_backend.database.session import get_db
from mm_xing.block import (o3101OutBlock, t1764OutBlock, t8401OutBlock,
                           t8424OutBlock, t8425OutBlock, t8426OutBlock,
                           t8436OutBlock, t9943OutBlock, t9944OutBlock)
from mm_xing.constant import TR_CODE_TO_TYPE
from mm_xing.tasks.master import (fetch_market_data, get_data_config,
                                  initialize_client)

router = APIRouter(
    prefix="/securies",
    tags=["securities"]
)

# Define a Union of all possible response models
ResponseModel = Union[
    t1764OutBlock, t8424OutBlock, t8425OutBlock, t8436OutBlock,
    t8401OutBlock, t8426OutBlock, t9943OutBlock, t9944OutBlock, o3101OutBlock
]

@router.get(
    "/code",
    response_model=List[ResponseModel],
    summary="Fetch Market Data by TR Code",
    description=(
        "Retrieve market data for a specified TR code. This endpoint checks if the data "
        "has already been fetched and stored in the database for the current day. If not, "
        "it fetches new data, stores it, and returns the result."
    ),
    responses={
        200: {
            "description": "Successful retrieval of market data.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "rank": 1,
                            "tradno": "001",
                            "tradname": "Example Trading Company"
                        }
                    ]
                }
            }
        },
        400: {
            "description": "Unsupported TR code provided.",
            "content": {
                "application/json": {
                    "example": {"detail": "Unsupported TR code: {tr_code}"}
                }
            }
        },
        404: {
            "description": "Data config code not found for the provided TR code.",
            "content": {
                "application/json": {
                    "example": {"detail": "Data config code not found for {tr_code}"}
                }
            }
        },
        500: {
            "description": "Internal server error occurred while fetching data.",
            "content": {
                "application/json": {
                    "example": {"detail": "Error message"}
                }
            }
        }
    }
)
async def fetch_code_data(
    tr_code: str = Query(..., description="The TR code representing the type of market data to fetch."),
    db: Session = Depends(get_db)
):
    """
    Fetch market data based on the provided TR code.

    This endpoint retrieves market data for a specific TR code. If the data has already been fetched
    and stored in the database for today, it returns the cached data. Otherwise, it fetches new data,
    stores it in the database, and returns the result.

    Args:
        tr_code (str): The TR code representing the type of market data to fetch.
        db (Session): The database session used for querying and storing data.

    Returns:
        List[ResponseModel]: A list of response models containing the market data.
    """
    # 오늘 날짜의 시작 시간
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 이미 실행된 태스크 확인
    tasks = db.query(RountineTaskOrm).filter(
        RountineTaskOrm.task_name == tr_code,
        RountineTaskOrm.status == 'done',
        RountineTaskOrm.created_at >= today_start
    ).all()

    if not tasks:
        data_config_code = get_data_config(config_type=TR_CODE_TO_TYPE[tr_code], tr_code=tr_code)
        if not data_config_code:
            raise HTTPException(status_code=404, detail=f"Data config code not found for {tr_code}")

        client, header = await initialize_client()
        try:
            data = await fetch_market_data(client, header, data_config_code)
            
            # TR 코드에 따른 적절한 ORM 모델 선택
            orm_model = get_orm_model_for_tr_code(tr_code)
            if not orm_model:
                raise HTTPException(status_code=400, detail=f"Unsupported TR code: {tr_code}")
            
            # 데이터 저장
            db.add_all([orm_model(**row.model_dump()) for row in data if row is not None])
            db.add(RountineTaskOrm(task_name=tr_code, status='done'))
            db.commit()
            return data
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            client.close()
    else:
        # 캐시된 데이터 반환
        orm_model = get_orm_model_for_tr_code(tr_code)
        cached_data = db.query(orm_model).filter(
            orm_model.created_at >= today_start
        ).all()
        return cached_data
    
def get_orm_model_for_tr_code(tr_code: str):
    """TR 코드에 따른 적절한 ORM 모델을 반환하는 함수"""
    orm_mapping = {
        't1764': t1764OutBlockOrm,
        't8424': t8424OutBlockOrm,
        't8425': t8425OutBlockOrm,
        't8436': t8436OutBlockOrm,
        't8401': t8401OutBlockOrm,
        't8426': t8426OutBlockOrm,
        't9943V': t9943VOutBlockOrm,
        't9943S': t9943SOutBlockOrm,
        't9943': t9943OutBlockOrm,
        't9944': t9944OutBlockOrm,
        'o3101': o3101OutBlockOrm,
    }
    return orm_mapping.get(tr_code)

def get_schema_model_for_tr_code(tr_code: str) -> Optional[Type[ResponseModel]]:
    """TR 코드에 따른 적절한 스키마 모델을 반환하는 함수"""
    schema_mapping: Dict[str, Type[ResponseModel]] = {
        't1764': t1764OutBlock,
        't8424': t8424OutBlock,
        't8425': t8425OutBlock,
        't8436': t8436OutBlock,
        't8401': t8401OutBlock,
        't8426': t8426OutBlock,
        't9943V': t9943OutBlock,
        't9943S': t9943OutBlock,
        't9943': t9943OutBlock,
        't9944': t9944OutBlock,
        'o3101': o3101OutBlock,
    }
    return schema_mapping.get(tr_code, None) 

        

    