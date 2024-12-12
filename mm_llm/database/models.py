import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, func

from mm_backend.database.base import Base


class BaseOrm(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=func.now(), nullable=True)

class CreditRiskPropertiesOrm(BaseOrm):
    __tablename__ = 'credit_risk_properties'

    id = Column(Integer, primary_key=True, autoincrement=True)
    grade = Column(String, nullable=False)
    tone = Column(String, nullable=False)
    major_signals = Column(JSON, nullable=False)
    keywords = Column(JSON, nullable=False)
    notable_points = Column(JSON, nullable=True)
    boundary_case_details = Column(JSON, nullable=True)
    article_id = Column(String, nullable=False, unique=True)
    article_published_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<CreditRiskPropertiesOrm(id={self.id}, grade={self.grade}, tone={self.tone})>"