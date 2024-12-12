from random import random
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from mm_crawler.database.models import NaverArticleContentOrm, NaverArticleListOrm, NaverResearchReportOrm
from mm_crawler.database.session import SessionLocal
from langchain_community.document_transformers.openai_functions import create_metadata_tagger
from langchain_openai import ChatOpenAI
from langchain import hub
from mm_llm.database.models import CreditRiskPropertiesOrm
from mm_llm.pgvector_retriever import DEFAULT_COLLECTION_NAME, init_vector_store
from langchain_core.documents import Document
import json

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
            "예: ‘법정관리’, ‘유동성 위기’, ‘신용등급 하락’ 영어로 작성해주세요.\n\n"
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

def get_report_by_id(report_id: int, sess: Session):
    report = sess.query(NaverResearchReportOrm).filter(NaverResearchReportOrm.id == str(report_id)).first()
    if report:
        return {
            "id": report.id,
            "title": report.title,
            "date": report.date,
            "issuer_company_name": report.issuer_company_name,
            "downloaded": report.downloaded,
            "created_at": report.created_at
        }
    print(f"Report with id {report_id} not found.")
    return None

from supabase import create_client, Client
from datetime import datetime
from mm_llm.config import settings

# Initialize the Supabase client
url = settings.PUBLIC_SUPABASE_URL
key = settings.PUBLIC_SUPABASE_ANON_KEY
supabase: Client = create_client(url, key)

# Add a new post with tags
def add_post_with_tags(post, tag_ids):
    # Insert the new post
    post_data = {
        "title": post["title"],
        "description": post["description"],
        "thumbnail": post["thumbnail"],
        "url": post["url"],
        "is_published": post["is_published"],
        "author_id": post["author_id"],
    }
    response = supabase.table("resources").insert(post_data).execute()
    post_id = response.data[0]["id"]

    # Link tags to the post
    resource_tags = [{"resource_id": post_id, "tag_id": tag_id} for tag_id in tag_ids]
    supabase.table("resource_tags").insert(resource_tags).execute()
    return post_id

# Add a new tag to an existing post
def add_tag_to_post(post_id, tag_name):
    # Check if the tag already exists, insert if not
    tag_response = supabase.table("tags").select("*").eq("name", tag_name).execute()
    if tag_response.data:
        tag_id = tag_response.data[0]["id"]
    else:
        tag_data = {
            "name": tag_name,
            "slug": tag_name.replace(" ", "-").lower(),
            # "index": None,
            "updated_at": datetime.utcnow().isoformat(),
        }
        tag_response = supabase.table("tags").insert(tag_data).execute()
        tag_id = tag_response.data[0]["id"]

    # Link the tag to the post
    supabase.table("resource_tags").insert({"resource_id": post_id, "tag_id": tag_id}).execute()
    return tag_id

# Add a tag independently
def add_tag_independently(tag_name):
    # Check if the tag already exists
    existing_tag = supabase.table("tags").select("*").eq("name", tag_name.replace(" ", "-").lower().strip()).execute().data
    if existing_tag:
        return existing_tag[0]["id"]
    tag_data = {
        "name": tag_name.replace(" ", "-").lower().strip(), 
        "slug": tag_name.replace(" ", "-").lower().strip(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    print(tag_data)
    print(existing_tag)
    response = supabase.table("tags").insert(tag_data).execute()
    return response.data

def save_credit_risk_properties(doc, sess: Session):
    # Create an instance of CreditRiskPropertiesOrm
    credit_risk_properties = CreditRiskPropertiesOrm(
        grade=doc['metadata']['grade'],
        tone=doc['metadata']['tone'],
        major_signals=doc['metadata']['major_signals'],
        keywords=doc['metadata']['keywords'],
        notable_points=doc['metadata'].get('notable_points', None),
        boundary_case_details=doc['metadata'].get('boundary_case_details', None),
        article_id=doc['metadata']['article_id'],
        article_published_at=doc['metadata']['article_published_at']
    )

    # Add the instance to the session
    sess.add(credit_risk_properties)

    # Commit the transaction to save the data
    sess.commit()

    print(f"Saved CreditRiskPropertiesOrm with article_id: {credit_risk_properties.article_id}")

def main():
    sess = SessionLocal()
    # llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    # document_transformer = create_metadata_tagger(CreditRiskProperties, llm=llm)
    # prompt = hub.pull("teddynote/metadata-tagger")
    # vector_store = init_vector_store(collection_name="naver_news_articles")
    # vs_filter = {}  # type: ignore
    # data = vector_store.similarity_search("중국", k=20, filter=vs_filter)
    # enhanced_documents = document_transformer.transform_documents(data[:5], prompt=prompt)
    # for doc in enhanced_documents:
    #     doc_ = doc.model_dump()
    #     # print(doc_.get('page_content', None))
    #     print(doc_['metadata'])

    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    prompt = hub.pull("teddynote/metadata-tagger")
    document_transformer = create_metadata_tagger(CreditRiskProperties, llm=llm)
    results = sess.query(NaverArticleContentOrm).join(
        NaverArticleListOrm, NaverArticleListOrm.article_id == NaverArticleContentOrm.article_id
    ).filter(NaverArticleListOrm.is_main == True).all()  # noqa: E712
    for ret in results[:]:
        page_content = f"{ret.title}\n{ret.content}"
        metadata = {
            "article_id": ret.article_id,
            "article_published_at": ret.article_published_at
        }
        doc = Document(page_content=page_content, metadata=metadata)
        enhanced_documents = document_transformer.transform_documents([doc], prompt=prompt)
        for enhanced_doc in enhanced_documents:
            doc = enhanced_doc.model_dump()
            grade = doc['metadata']['grade']
            if grade in ['A', 'B', 'C']:
                post = {
                    "title": str(ret.title),
                    "description": (
                        "### 주요 진호\n" +
                        "\n".join(f"- {signal}" for signal in doc['metadata']['major_signals']) +
                        "\n\n### 주목할 만한 점\n" +
                        "\n".join(f"- {point}" for point in doc['metadata']['notable_points'])
                    ),
                    "thumbnail": "",
                    "url": f"https://n.news.naver.com/mnews/article/{ret.media_id}/{ret.article_id}",
                    "is_published": True,
                    "author_id": "0fc79224-7139-49c4-a6dc-124180a0334f"
                }
                tag_ids = []
                tag_slug = f"리스크평가-{grade}"
                tag_ids.append(add_tag_independently(tag_slug))
                # keywords = doc['metadata']['keywords']
                # for keyword in keywords:
                #     tag_id = add_tag_independently(keyword)
                #     if tag_id:
                #         tag_ids.append(tag_id)
                post_id = add_post_with_tags(post, tag_ids)
                print(f"Post ID: {post_id}")
                print("Tags added.")
    sess.close()
    
if __name__ == "__main__":
    main()