"""remove embeddings

Revision ID: 124d717f8267
Revises: 52662ec8a6e5
Create Date: 2024-12-10 16:21:38.667349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '124d717f8267'
down_revision: Union[str, None] = '52662ec8a6e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
import pgvector.sqlalchemy


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('xing_t8401_outblock')
    op.drop_table('xing_t1764_outblock')
    op.drop_table('xing_t8436_outblock')
    op.drop_table('xing_t8424_outblock')
    op.drop_table('xing_t9943_outblock')
    op.drop_table('xing_o3101_outblock')
    op.drop_table('xing_t8426_outblock')
    op.drop_table('xing_t9943S_outblock')
    op.drop_table('xing_t9944_outblock')
    op.drop_table('xing_t9943V_outblock')
    op.drop_table('xing_t8425_outblock')
    op.drop_table('routine_tasks')
    op.add_column('naver_article_chunks', sa.Column('embedded_at', sa.DateTime(timezone=True), nullable=True))
    op.drop_column('naver_article_chunks', 'content_embedding')
    op.drop_column('naver_article_contents', 'embedded_at')
    op.add_column('naver_research_report_chunks', sa.Column('embedded_at', sa.DateTime(timezone=True), nullable=True))
    op.drop_column('naver_research_report_chunks', 'content_embedding')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('naver_research_report_chunks', sa.Column('content_embedding', pgvector.sqlalchemy.Vector(dim=3072), autoincrement=False, nullable=False))
    op.drop_column('naver_research_report_chunks', 'embedded_at')
    op.add_column('naver_article_contents', sa.Column('embedded_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('naver_article_chunks', sa.Column('content_embedding', pgvector.sqlalchemy.Vector(dim=3072), autoincrement=False, nullable=False))
    op.drop_column('naver_article_chunks', 'embedded_at')
    op.create_table('routine_tasks',
    sa.Column('task_name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='routine_tasks_pkey')
    )
    op.create_table('xing_t8425_outblock',
    sa.Column('tmname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='테마명'),
    sa.Column('tmcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='테마코드'),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t8425_outblock_pkey')
    )
    op.create_table('xing_t9943V_outblock',
    sa.Column('hname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목명'),
    sa.Column('shcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='단축코드'),
    sa.Column('expcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='확장코드'),
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"xing_t9943V_outblock_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t9943V_outblock_pkey')
    )
    op.create_table('xing_t9944_outblock',
    sa.Column('hname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목명'),
    sa.Column('shcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='단축코드'),
    sa.Column('expcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='확장코드'),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t9944_outblock_pkey')
    )
    op.create_table('xing_t9943S_outblock',
    sa.Column('hname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목명'),
    sa.Column('shcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='단축코드'),
    sa.Column('expcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='확장코드'),
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"xing_t9943S_outblock_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t9943S_outblock_pkey')
    )
    op.create_table('xing_t8426_outblock',
    sa.Column('hname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목명'),
    sa.Column('shcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='단축코드'),
    sa.Column('expcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='확장코드'),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t8426_outblock_pkey')
    )
    op.create_table('xing_o3101_outblock',
    sa.Column('Symbol', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목코드'),
    sa.Column('SymbolNm', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목명'),
    sa.Column('ApplDate', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목배치수신일(한국일자)'),
    sa.Column('BscGdsCd', sa.VARCHAR(), autoincrement=False, nullable=False, comment='기초상품코드'),
    sa.Column('BscGdsNm', sa.VARCHAR(), autoincrement=False, nullable=False, comment='기초상품명'),
    sa.Column('ExchCd', sa.VARCHAR(), autoincrement=False, nullable=False, comment='거래소코드'),
    sa.Column('ExchNm', sa.VARCHAR(), autoincrement=False, nullable=False, comment='거래소명'),
    sa.Column('CrncyCd', sa.VARCHAR(), autoincrement=False, nullable=False, comment='기준통화코드'),
    sa.Column('NotaCd', sa.VARCHAR(), autoincrement=False, nullable=False, comment='진법구분코드'),
    sa.Column('UntPrc', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, comment='호가단위가격'),
    sa.Column('MnChgAmt', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, comment='최소가격변동금액'),
    sa.Column('RgltFctr', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, comment='가격조정계수'),
    sa.Column('CtrtPrAmt', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, comment='계약당금액'),
    sa.Column('GdsCd', sa.VARCHAR(), autoincrement=False, nullable=False, comment='상품구분코드'),
    sa.Column('LstngYr', sa.VARCHAR(), autoincrement=False, nullable=False, comment='월물(년)'),
    sa.Column('LstngM', sa.VARCHAR(), autoincrement=False, nullable=False, comment='월물(월)'),
    sa.Column('EcPrc', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, comment='정산가격'),
    sa.Column('DlStrtTm', sa.VARCHAR(), autoincrement=False, nullable=False, comment='거래시작시간'),
    sa.Column('DlEndTm', sa.VARCHAR(), autoincrement=False, nullable=False, comment='거래종료시간'),
    sa.Column('DlPsblCd', sa.VARCHAR(), autoincrement=False, nullable=False, comment='거래가능구분코드'),
    sa.Column('MgnCltCd', sa.VARCHAR(), autoincrement=False, nullable=False, comment='증거금징수구분코드'),
    sa.Column('OpngMgn', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, comment='개시증거금'),
    sa.Column('MntncMgn', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, comment='유지증거금'),
    sa.Column('OpngMgnR', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, comment='개시증거금율'),
    sa.Column('MntncMgnR', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False, comment='유지증거금율'),
    sa.Column('DotGb', sa.INTEGER(), autoincrement=False, nullable=False, comment='유효소수점자리수'),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_o3101_outblock_pkey')
    )
    op.create_table('xing_t9943_outblock',
    sa.Column('hname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목명'),
    sa.Column('shcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='단축코드'),
    sa.Column('expcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='확장코드'),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t9943_outblock_pkey')
    )
    op.create_table('xing_t8424_outblock',
    sa.Column('hname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='업종명'),
    sa.Column('upcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='업종코드'),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t8424_outblock_pkey')
    )
    op.create_table('xing_t8436_outblock',
    sa.Column('hname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목명'),
    sa.Column('shcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='단축코드'),
    sa.Column('expcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='확장코드'),
    sa.Column('etfgubun', sa.VARCHAR(), autoincrement=False, nullable=False, comment='ETF구분(1:ETF2:ETN)'),
    sa.Column('uplmtprice', sa.INTEGER(), autoincrement=False, nullable=False, comment='상한가'),
    sa.Column('dnlmtprice', sa.INTEGER(), autoincrement=False, nullable=False, comment='하한가'),
    sa.Column('jnilclose', sa.INTEGER(), autoincrement=False, nullable=False, comment='전일가'),
    sa.Column('memedan', sa.VARCHAR(), autoincrement=False, nullable=False, comment='주문수량단위'),
    sa.Column('recprice', sa.INTEGER(), autoincrement=False, nullable=False, comment='기준가'),
    sa.Column('gubun', sa.VARCHAR(), autoincrement=False, nullable=False, comment='구분(1:코스피2:코스닥)'),
    sa.Column('bu12gubun', sa.VARCHAR(), autoincrement=False, nullable=False, comment='증권그룹'),
    sa.Column('spac_gubun', sa.VARCHAR(), autoincrement=False, nullable=False, comment='기업인수목적회사여부(Y/N)'),
    sa.Column('filler', sa.VARCHAR(), autoincrement=False, nullable=False, comment='filler(미사용)'),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t8436_outblock_pkey')
    )
    op.create_table('xing_t1764_outblock',
    sa.Column('rank', sa.INTEGER(), autoincrement=False, nullable=False, comment='순위'),
    sa.Column('tradno', sa.VARCHAR(), autoincrement=False, nullable=False, comment='거래원번호'),
    sa.Column('tradname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='거래원이름'),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t1764_outblock_pkey')
    )
    op.create_table('xing_t8401_outblock',
    sa.Column('hname', sa.VARCHAR(), autoincrement=False, nullable=False, comment='종목명'),
    sa.Column('shcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='단축코드'),
    sa.Column('expcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='확장코드'),
    sa.Column('BaseOrmcode', sa.VARCHAR(), autoincrement=False, nullable=False, comment='기초자산코드'),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='xing_t8401_outblock_pkey')
    )
    # ### end Alembic commands ###
