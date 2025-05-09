from datetime import datetime
from typing import Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from mm_xing.database.models import (
    RountineTaskOrm,
    o3101OutBlockOrm,
    t1764OutBlockOrm,
    t8401OutBlockOrm,
    t8424OutBlockOrm,
    t8425OutBlockOrm,
    t8426OutBlockOrm,
    t8436OutBlockOrm,
    t9943OutBlockOrm,
    t9943SOutBlockOrm,
    t9943VOutBlockOrm,
    t9944OutBlockOrm,
)
from mm_xing.database.session import get_db
from mm_xing.block import (
    o3101OutBlock,
    t1764OutBlock,
    t8401OutBlock,
    t8424OutBlock,
    t8425OutBlock,
    t8426OutBlock,
    t8436OutBlock,
    t9943OutBlock,
    t9944OutBlock,
)
from mm_xing.constant import TR_CODE_TO_TYPE
from mm_xing.tasks.master import fetch_market_data, get_data_config, initialize_client

router = APIRouter(prefix="/securities", tags=["securities"])

# Define a Union of all possible response models
ResponseModel = Union[
    t1764OutBlock,
    t8424OutBlock,
    t8425OutBlock,
    t8436OutBlock,
    t8401OutBlock,
    t8426OutBlock,
    t9943OutBlock,
    t9944OutBlock,
    o3101OutBlock,
]

# ---------- centralised registry for TR-code models ----------

# An immutable pair to hold the ORM and its corresponding Pydantic schema.


@dataclass(frozen=True)
class TRModelPair:
    orm: Type
    schema: Type[ResponseModel]


# Mapping of TR code ➜ (ORM model, Pydantic schema)
TR_MODEL_REGISTRY: Dict[str, TRModelPair] = {
    "t1764": TRModelPair(t1764OutBlockOrm, t1764OutBlock),
    "t8424": TRModelPair(t8424OutBlockOrm, t8424OutBlock),
    "t8425": TRModelPair(t8425OutBlockOrm, t8425OutBlock),
    "t8436": TRModelPair(t8436OutBlockOrm, t8436OutBlock),
    "t8401": TRModelPair(t8401OutBlockOrm, t8401OutBlock),
    "t8426": TRModelPair(t8426OutBlockOrm, t8426OutBlock),
    "t9943V": TRModelPair(t9943VOutBlockOrm, t9943OutBlock),
    "t9943S": TRModelPair(t9943SOutBlockOrm, t9943OutBlock),
    "t9943": TRModelPair(t9943OutBlockOrm, t9943OutBlock),
    "t9944": TRModelPair(t9944OutBlockOrm, t9944OutBlock),
    "o3101": TRModelPair(o3101OutBlockOrm, o3101OutBlock),
}


class TRCode(str, Enum):
    """Enum representation for supported TR codes."""

    t1764 = "t1764"
    t8424 = "t8424"
    t8425 = "t8425"
    t8436 = "t8436"
    t8401 = "t8401"
    t8426 = "t8426"
    t9943V = "t9943V"
    t9943S = "t9943S"
    t9943 = "t9943"
    t9944 = "t9944"
    o3101 = "o3101"


# ----------------------------------------------------------------------


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
                            "tradname": "Example Trading Company",
                        }
                    ]
                }
            },
        },
        400: {
            "description": "Unsupported TR code provided.",
            "content": {
                "application/json": {
                    "example": {"detail": "Unsupported TR code: {tr_code}"}
                }
            },
        },
        404: {
            "description": "Data config code not found for the provided TR code.",
            "content": {
                "application/json": {
                    "example": {"detail": "Data config code not found for {tr_code}"}
                }
            },
        },
        500: {
            "description": "Internal server error occurred while fetching data.",
            "content": {"application/json": {"example": {"detail": "Error message"}}},
        },
    },
)
async def fetch_code_data(
    tr_code: TRCode = Query(
        ..., description="The TR code representing the type of market data to fetch."
    ),
    limit: int = Query(100, description="The maximum number of records to return."),
    db: Session = Depends(get_db),
):
    """Fetch market data for a given TR code (Enum-based)."""

    # Convert Enum ➜ str for internal usage
    tr_code_str = str(tr_code)

    # 오늘 날짜의 시작 시간
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 이미 실행된 태스크 확인
    tasks = (
        db.query(RountineTaskOrm)
        .filter(
            RountineTaskOrm.task_name == tr_code_str,
            RountineTaskOrm.status == "done",
            RountineTaskOrm.created_at >= today_start,
        )
        .all()
    )

    if not tasks:
        try:
            data_config_code = get_data_config(
                config_type=TR_CODE_TO_TYPE[tr_code_str], tr_code=tr_code_str
            )
        except KeyError:
            raise HTTPException(
                status_code=400, detail=f"Unsupported TR code: {tr_code_str}"
            )
        if not data_config_code:
            raise HTTPException(
                status_code=404, detail=f"Data config code not found for {tr_code_str}"
            )

        client, header = await initialize_client()
        try:
            data = await fetch_market_data(client, header, data_config_code)

            # TR 코드에 따른 적절한 ORM 모델 선택
            orm_model = get_orm_model_for_tr_code(tr_code_str)
            if not orm_model:
                raise HTTPException(
                    status_code=400, detail=f"Unsupported TR code: {tr_code_str}"
                )

            # 데이터 저장
            db.add_all(
                [orm_model(**row.model_dump()) for row in data if row is not None]
            )
            db.add(RountineTaskOrm(task_name=tr_code_str, status="done"))
            db.commit()
            return data[:limit]
        except Exception as e:
            db.rollback()
            # {'detail': '"Response does not contain expected outblock data: {\'rsp_cd\': \'00000\', \'rsp_msg\': \'해당자료가 없습니다.\'}"'}
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            client.close()
    else:
        # 캐시된 데이터 반환
        orm_model = get_orm_model_for_tr_code(tr_code_str)
        if orm_model is None:
            raise HTTPException(
                status_code=400, detail=f"Unsupported TR code: {tr_code_str}"
            )
        cached_data = (
            db.query(orm_model)
            .filter(
                orm_model.created_at >= today_start  # type: ignore
            )
            .limit(limit)
            .all()
        )
        return cached_data


def get_orm_model_for_tr_code(tr_code: str):
    """Return the ORM model associated with the given TR code."""
    pair = TR_MODEL_REGISTRY.get(tr_code)
    return pair.orm if pair else None


def get_schema_model_for_tr_code(tr_code: str) -> Optional[Type[ResponseModel]]:
    """Return the Pydantic schema associated with the given TR code."""
    pair = TR_MODEL_REGISTRY.get(tr_code)
    return pair.schema if pair else None
