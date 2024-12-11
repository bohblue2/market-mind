from mm_crawler.database.models import NaverResearchReportOrm
from mm_crawler.database.session import SessionLocal
from langchain_community.document_transformers.openai_functions import create_metadata_tagger
from langchain_openai import ChatOpenAI
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from langchain import hub
from sqlalchemy.orm import Session
import json

from mm_llm.pgvector_retriever import DEFAULT_COLLECTION_NAME, init_vector_store

class CreditRiskProperties(BaseModel):
    grade: Literal["A", "B", "C", "D", "F"] = Field(
        description=(
            "기사의 전반적 내용을 기반으로 부도 위험 수준을 A/B/C/D/F 등급 중 하나로 분류한 값.\n\n"
            "• A: 매우 위험 (법정관리 신청, 파산 등 명확한 지급불능 상황)\n"
            "• B: 위험 (장기간 대규모 적자, 감사의견 거절, 자율협약 추진 등 단기간 내 부도 가능성 시사)\n"
            "• C: 주의 (영업적자 전환, 신용등급 소폭 하락, 단기 유동성 악화 등 중장기적 위험요소 존재)\n"
            "• D: 관찰 (경영진 교체, 시장점유율 하락 등 직접적인 부도 위험도는 낮으나 우려되는 정황)\n"
            "• F: 무관 (부도 위험과 직접 연관 없는 단순 기업 소식, 신제품 출시, 업계 동향)"
        )
    )
    
    # 평가의 톤: 긍정적 혹은 부정적
    tone: Literal["positive", "negative"]

    major_signals: List[str] = Field(
        description=(
            "기사 내에서 부도 위험성을 시사하는 핵심적 신호나 사건, 수치 등을 나열하는 목록.\n\n"
            "예: ‘법정관리 신청’, ‘신용등급 3단계 하락’, ‘장기간 대규모 적자’, ‘일시적 실적 부진’ 등"
        )
    )

    reasoning: Dict[str, Any] = Field(
        description=(
            "등급 부여 근거를 체계적으로 제시하기 위한 구조화된 정보.\n\n"
            "이 필드는 템플릿 기반 근거, 점수화 방식, 키워드 매칭 등을 모두 포괄하는 설명을 담는다. "
            "예를 들어, 등급별 핵심 기준에 기사 내용을 매핑한 템플릿 정보, 각 신호별 가중치 점수 합산 결과, "
            "키워드 매칭 분석 결과를 명시할 수 있다.\n\n"
            "예시 구조:\n"
            "{\n"
            "  'template_reference': 'v1.0',\n"
            "  'matched_criteria': [\"법정관리 신청: A등급 핵심 신호 매칭\", \"신용등급 3단계 하락: A등급 조건 충족\"],\n"
            "  'scoring_details': {\"법정관리 신청\": +10, \"신용등급 3단계 하락\": +5, \"total_score\": 15},\n"
            "  'keywords_analysis': {\n"
            "    \"등급A관련키워드\": [\"법정관리\", \"파산\"],\n"
            "    \"기사내발견키워드\": [\"법정관리\"],\n"
            "    \"매칭결과\": \"A등급 근거 강화\"\n"
            "  },\n"
            "  'final_reason': \"법정관리 신청과 급격한 신용등급 하락으로 A등급 부여\"\n"
            "}"
        )
    )

    keywords: List[str] = Field(
        description=(
            "기사 내에서 빈번히 등장하거나 부도 위험과 연관된 단어, 표현, 개념 등을 담는 목록.\n\n"
            "예: ‘법정관리’, ‘유동성 위기’, ‘신용등급 하락’"
        )
    )

    notable_points: Optional[List[str]] = Field(
        description=(
            "기사 내 특이하거나 참조할 만한 부차적 정보를 담는 목록.\n\n"
            "등급 결정에 직접적이지는 않지만, 참고용으로 활용할 수 있는 요소를 포함한다.\n"
            "예: ‘경영진 교체 발표’, ‘시장 전반 불황’, ‘신규 사업 진출 고려’"
        )
    )

    boundary_case_details: Optional[Dict[str, Any]] = Field(
        description=(
            "경계 사례(등급 간 모호한 상황) 발생 시 적용한 추가 규칙이나 예외 처리에 대한 정보를 담는 구조.\n\n"
            "이를 통해 경계 사례에서 어떤 우선순위 신호나 예외 규칙이 적용되었는지 기록하고, "
            "향후 일관성 있는 개선 및 판단을 지원한다.\n\n"
            "예:\n"
            "{\n"
            "  'boundary_case_handling': True,\n"
            "  'reason': \"A/B 경계 상황에서 '감사의견 거절' 신호가 발견되어 B등급 근거 강화\",\n"
            "  'applied_rules': [\"감사의견 거절 시 B등급 상향 규칙 적용\"]\n"
            "}"
        )
    )
    
sess = SessionLocal()

llm=ChatOpenAI(temperature=0, model="gpt-4o-mini")
document_transformer = create_metadata_tagger(CreditRiskProperties, llm=llm)
prompt = hub.pull("teddynote/metadata-tagger")

vector_store = init_vector_store(collection_name=DEFAULT_COLLECTION_NAME)
vs_filter = {"chunk_num": {"$in": [1,2,3,4,5]}} 
vs_filter = None
data = vector_store.similarity_search("부도", k=20, filter=vs_filter)
enhanced_documents = document_transformer.transform_documents(data[:5], prompt=prompt)
# print(json.dumps([doc.dict() for doc in enhanced_documents], indent=4, ensure_ascii=False))

def get_report_by_id(report_id: int, sess: Session):
    # Query the database for the report with the given report_id
    report = sess.query(NaverResearchReportOrm).filter(NaverResearchReportOrm.id == str(report_id)).first()
    
    if report:
        # Convert the report to a dictionary or JSON format
        report_data = {
            "id": report.id,
            "title": report.title,
            "date": report.date,
            "issuer_company_name": report.issuer_company_name,
            "downloaded": report.downloaded,
            "created_at": report.created_at
        }
        print(report_data)
        return report_data
    else:
        print(f"Report with id {report_id} not found.")
        return None


for doc in enhanced_documents:
    # print(doc.dict())
    doc=doc.dict()
    get_report_by_id(doc["metadata"]['report_id'], sess)
