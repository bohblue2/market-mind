import datetime

from sqlalchemy import Column, Integer, String, DateTime
from mm_backend.database.base import Base

class RountineTaskOrm(Base):
    __tablename__ = 'routine_tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=True)

    def __repr__(self):
        return f"<RountineTaskOrm(id={self.id}, task_name='{self.task_name}', status='{self.status}')>"
    
class T1764OutBlockOrm(Base):
    __tablename__ = 't1764_outblock'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rank = Column(Integer, nullable=False, default=0, comment='순위')  
    tradno = Column(String, nullable=False, default='', comment='거래원번호')
    tradname = Column(String, nullable=False, default='', comment='거래원이름')
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=True)

    def __repr__(self):
        return f"<T1764OutBlockOrm(id={self.id}, rank={self.rank}, tradno='{self.tradno}', tradname='{self.tradname}')>"

