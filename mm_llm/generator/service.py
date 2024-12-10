
# import os
# from typing import Optional

# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import PromptTemplate
# from langchain_core.runnables import RunnablePassthrough
# from langchain_milvus import Zilliz
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# from mm_llm.constant import DEFAULT_EMBEDDING_MODEL
# from mm_llm.prompts.default import PROMPT_TEMPLATE
# from mm_llm.spliter import format_docs
# from mm_llm.vectorstore.milvus import (get_milvus_client,
#                                        get_naver_news_article_collection)


# class GeneratorService:
#     def __init__(self):
#         self._client = get_milvus_client()
#         collection = get_naver_news_article_collection()
#         vectorstore = Zilliz(
#             embedding_function = OpenAIEmbeddings(model=DEFAULT_EMBEDDING_MODEL),
#             collection_name = collection.name,
#             connection_args = {
#                 "uri": os.getenv("MILVUS_URI"),
#                 "token": os.getenv("MILVUS_API_KEY")
#             },
#             primary_field="article_id",
#             vector_field="content_embedding",
#             text_field="content",
#             drop_old=False
#         )
#         retriever = vectorstore.as_retriever()
#         llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
#         prompt = PromptTemplate(
#             template=PROMPT_TEMPLATE, input_variables=["context", "question"]
#         )
#         self._rag_chain = (
#             {"context": retriever | format_docs, "question": RunnablePassthrough()}
#             | prompt
#             | llm
#             | StrOutputParser()
#         )

#     def generate_answer(self, content: str, prompt_template: Optional[str] = "") -> str:
#         return self._rag_chain.invoke(
#             f"다음과 같은 프롬프트에 맞춰서 답변해야합니다:'{prompt_template}' 프롬프트가 비어있다면 신경쓰지 마세요. \
#             그리고\n질문에: {content} 에 대한 답변을 작성해주세요."
#         )
    
#     def close(self):
#         self._client.close()

# def get_generator_service():
#     service = GeneratorService()
#     try:
#         yield service
#     finally:
#         service.close()