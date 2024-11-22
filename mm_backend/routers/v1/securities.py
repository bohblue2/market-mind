from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from mm_backend.database.session import get_db
from mm_xing.constant import TR_CODE_TO_TYPE
from mm_xing.tasks.master import fetch_market_data, get_data_config, initialize_client
from mm_backend.database.models import RountineTaskOrm, o3101OutBlockOrm, t1764OutBlockOrm, t8401OutBlockOrm, t8424OutBlockOrm, t8425OutBlockOrm, t8426OutBlockOrm, t8436OutBlockOrm, t9943OutBlockOrm, t9943SOutBlockOrm, t9943VOutBlockOrm, t9944OutBlockOrm
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/securies",
    tags=["securities"]
)

@router.get(
    "/code")
async def fetch_code_data(
    tr_code: str, 
    db: Session = Depends(get_db)
):
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

        
    

        

    