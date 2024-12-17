import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, func

from mm_backend.database.base import Base


class BaseOrm(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CreditRiskPropertiesOrm(BaseOrm):
    __tablename__ = 'credit_risk_properties'

    id = Column(Integer, primary_key=True, autoincrement=True)
    grade = Column(String)
    tone = Column(String)
    major_signals = Column(Text)
    keywords = Column(Text)
    notable_points = Column(Text)
    boundary_case_details = Column(Text)
    article_id = Column(String)
    article_published_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<CreditRiskPropertiesOrm(id={self.id}, grade={self.grade}, tone={self.tone})>"