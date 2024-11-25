import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from mm_backend.database.base import Base


class BaseOrm(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=True)

class RountineTaskOrm(BaseOrm):
    __tablename__ = 'routine_tasks'
    task_name = Column(String, nullable=False)
    status = Column(String, nullable=False)

    def __repr__(self):
        return f"<RountineTaskOrm(id={self.id}, task_name='{self.task_name}', status='{self.status}')>"
    
class t1764OutBlockOrm(BaseOrm):
    __tablename__ = 't1764_outblock'
    rank = Column(Integer, nullable=False, default=0, comment='순위')  
    tradno = Column(String, nullable=False, default='', comment='거래원번호')
    tradname = Column(String, nullable=False, default='', comment='거래원이름')

    def __repr__(self):
        return f"<T1764OutBlockOrm(id={self.id}, rank={self.rank}, tradno='{self.tradno}', tradname='{self.tradname}')>"

class t8424OutBlockOrm(BaseOrm):
    __tablename__ = 't8424_outblock'
    hname = Column(String, nullable=False, default='', comment='업종명')
    upcode = Column(String, nullable=False, default='', comment='업종코드')

    def __repr__(self):
        return f"<T8424OutBlockOrm(id={self.id}, hname='{self.hname}', upcode='{self.upcode}')>"

class t8425OutBlockOrm(BaseOrm):
    __tablename__ = 't8425_outblock'
    tmname = Column(String, nullable=False, default='', comment='테마명')
    tmcode = Column(String, nullable=False, default='', comment='테마코드')

    def __repr__(self):
        return f"<T8425OutBlockOrm(id={self.id}, tmname='{self.tmname}', tmcode='{self.tmcode}')>"

class t8436OutBlockOrm(BaseOrm):
    __tablename__ = 't8436_outblock'
    hname = Column(String, nullable=False, default='', comment='종목명')
    shcode = Column(String, nullable=False, default='', comment='단축코드')
    expcode = Column(String, nullable=False, default='', comment='확장코드')
    etfgubun = Column(String, nullable=False, default='', comment='ETF구분(1:ETF2:ETN)')
    uplmtprice = Column(Integer, nullable=False, default=0, comment='상한가')
    dnlmtprice = Column(Integer, nullable=False, default=0, comment='하한가')
    jnilclose = Column(Integer, nullable=False, default=0, comment='전일가')
    memedan = Column(String, nullable=False, default='', comment='주문수량단위')
    recprice = Column(Integer, nullable=False, default=0, comment='기준가')
    gubun = Column(String, nullable=False, default='', comment='구분(1:코스피2:코스닥)')
    bu12gubun = Column(String, nullable=False, default='', comment='증권그룹')
    spac_gubun = Column(String, nullable=False, default='', comment='기업인수목적회사여부(Y/N)')
    filler = Column(String, nullable=False, default='', comment='filler(미사용)')

    def __repr__(self):
        return f"<T8436OutBlockOrm(id={self.id}, hname='{self.hname}', shcode='{self.shcode}')>"

class t8401OutBlockOrm(BaseOrm):
    __tablename__ = 't8401_outblock'
    hname = Column(String, nullable=False, default='', comment='종목명')
    shcode = Column(String, nullable=False, default='', comment='단축코드')
    expcode = Column(String, nullable=False, default='', comment='확장코드')
    BaseOrmcode = Column(String, nullable=False, default='', comment='기초자산코드')

    def __repr__(self):
        return f"<T8401OutBlockOrm(id={self.id}, hname='{self.hname}', shcode='{self.shcode}')>"

class t8426OutBlockOrm(BaseOrm):
    __tablename__ = 't8426_outblock'
    hname = Column(String, nullable=False, default='', comment='종목명')
    shcode = Column(String, nullable=False, default='', comment='단축코드')
    expcode = Column(String, nullable=False, default='', comment='확장코드')

    def __repr__(self):
        return f"<T8426OutBlockOrm(id={self.id}, hname='{self.hname}', shcode='{self.shcode}')>"

class t9943VOutBlockOrm(BaseOrm):
    __tablename__ = 't9943V_outblock'
    hname = Column(String, nullable=False, default='', comment='종목명')
    shcode = Column(String, nullable=False, default='', comment='단축코드') 
    expcode = Column(String, nullable=False, default='', comment='확장코드')

    def __repr__(self):
        return f"<T9943VOutBlockOrm(id={self.id}, hname='{self.hname}', shcode='{self.shcode}')>"

class t9943SOutBlockOrm(BaseOrm):
    __tablename__ = 't9943S_outblock'
    hname = Column(String, nullable=False, default='', comment='종목명')
    shcode = Column(String, nullable=False, default='', comment='단축코드') 
    expcode = Column(String, nullable=False, default='', comment='확장코드')

    def __repr__(self):
        return f"<T9943SOutBlockOrm(id={self.id}, hname='{self.hname}', shcode='{self.shcode}')>"

class t9943OutBlockOrm(BaseOrm):
    __tablename__ = 't9943_outblock'
    hname = Column(String, nullable=False, default='', comment='종목명')
    shcode = Column(String, nullable=False, default='', comment='단축코드') 
    expcode = Column(String, nullable=False, default='', comment='확장코드')

    def __repr__(self):
        return f"<T9943OutBlockOrm(id={self.id}, hname='{self.hname}', shcode='{self.shcode}')>"



class t9944OutBlockOrm(BaseOrm):
    __tablename__ = 't9944_outblock'
    hname = Column(String, nullable=False, default='', comment='종목명')
    shcode = Column(String, nullable=False, default='', comment='단축코드')
    expcode = Column(String, nullable=False, default='', comment='확장코드')

    def __repr__(self):
        return f"<T9944OutBlockOrm(id={self.id}, hname='{self.hname}', shcode='{self.shcode}')>"

class o3101OutBlockOrm(BaseOrm):
    __tablename__ = 'o3101_outblock'
    Symbol = Column(String, nullable=False, default='', comment='종목코드')
    SymbolNm = Column(String, nullable=False, default='', comment='종목명')
    ApplDate = Column(String, nullable=False, default='', comment='종목배치수신일(한국일자)')
    BscGdsCd = Column(String, nullable=False, default='', comment='기초상품코드')
    BscGdsNm = Column(String, nullable=False, default='', comment='기초상품명')
    ExchCd = Column(String, nullable=False, default='', comment='거래소코드')
    ExchNm = Column(String, nullable=False, default='', comment='거래소명')
    CrncyCd = Column(String, nullable=False, default='', comment='기준통화코드')
    NotaCd = Column(String, nullable=False, default='', comment='진법구분코드')
    UntPrc = Column(Float, nullable=False, default=0.0, comment='호가단위가격')
    MnChgAmt = Column(Float, nullable=False, default=0.0, comment='최소가격변동금액')
    RgltFctr = Column(Float, nullable=False, default=0.0, comment='가격조정계수')
    CtrtPrAmt = Column(Float, nullable=False, default=0.0, comment='계약당금액')
    GdsCd = Column(String, nullable=False, default='', comment='상품구분코드')
    LstngYr = Column(String, nullable=False, default='', comment='월물(년)')
    LstngM = Column(String, nullable=False, default='', comment='월물(월)')
    EcPrc = Column(Float, nullable=False, default=0.0, comment='정산가격')
    DlStrtTm = Column(String, nullable=False, default='', comment='거래시작시간')
    DlEndTm = Column(String, nullable=False, default='', comment='거래종료시간')
    DlPsblCd = Column(String, nullable=False, default='', comment='거래가능구분코드')
    MgnCltCd = Column(String, nullable=False, default='', comment='증거금징수구분코드')
    OpngMgn = Column(Float, nullable=False, default=0.0, comment='개시증거금')
    MntncMgn = Column(Float, nullable=False, default=0.0, comment='유지증거금')
    OpngMgnR = Column(Float, nullable=False, default=0.0, comment='개시증거금율')
    MntncMgnR = Column(Float, nullable=False, default=0.0, comment='유지증거금율')
    DotGb = Column(Integer, nullable=False, default=0, comment='유효소수점자리수')

    def __repr__(self):
        return f"<O3101OutBlockOrm(id={self.id}, Symbol='{self.Symbol}', SymbolNm='{self.SymbolNm}')>"
