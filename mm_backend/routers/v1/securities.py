from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException

from mm_backend.constant import LATEST_INDEX
from mm_backend.database.session import get_db
from mm_backend.schemas import ChatCompletionResponse, ChatRequest, RoleEnum
from mm_llm.generator import GeneratorService, get_generator_service
from mm_xing.tasks.master import fetch_market_data, get_data_config_code, initialize_client
from mm_backend.database.models import RountineTaskOrm, T1764OutBlockOrm
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/securies",
    tags=["securities"]
)

@router.get(
    "/code"
    # response_model=
)
async def fetch_code_data(
    tr_code: str, 
    db: Session = Depends(get_db)
):
    tasks = db.query(RountineTaskOrm).filter(
        RountineTaskOrm.task_name == tr_code,
        RountineTaskOrm.status == 'done',
        RountineTaskOrm.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ).all()

    if not tasks:
        data_config_code = get_data_config_code(tr_code)
        if not data_config_code:
            raise HTTPException(status_code=404, detail="Data config code not found")

        client, header = await initialize_client()
        try:
            ret = await fetch_market_data(client, header, data_config_code)
            print(ret)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        else:
            try:
                db.add_all([T1764OutBlockOrm(**row.model_dump()) for row in ret if row is not None])
                db.add(RountineTaskOrm(task_name=tr_code, status='done'))
                db.commit()
            except  Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=str(e))
        finally:
            client.close()
    else:
        print(tasks)

        

    