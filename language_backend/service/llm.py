
import os
from typing import Optional

from pymilvus import MilvusClient

from language_backend.vectorstore import get_naver_news_article_collection, get_client
from langchain_milvus.retrievers import MilvusCollectionHybridSearchRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_milvus.retrievers import MilvusCollectionHybridSearchRetriever
from langchain_milvus.utils.sparse import BM25SparseEmbedding
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

PROMPT_TEMPLATE = """
Human: You are an AI assistant, and provides answers to questions by using fact based and statistical information when possible.
Use the following pieces of information to provide a concise answer to the question enclosed in <question> tags.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
<context>
{context}
</context>

<question>
{question}
</question>

The response should be specific and use statistics or numbers when possible.

Write the answer in korean.

Assistant:"""

# Create a PromptTemplate instance with the defined template and input variables
prompt = PromptTemplate(
    template=PROMPT_TEMPLATE, input_variables=["context", "question"]
)
from langchain_milvus import Milvus, Zilliz


# Define a function to format the retrieved documents
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

class LlmService:
    def __init__(self):
        self._client: MilvusClient = get_client()
        collection = get_naver_news_article_collection()
        milvus_store = Zilliz(
            embedding_function = OpenAIEmbeddings(model="text-embedding-3-large"),
            collection_name = collection.name,
            connection_args = {
                "uri": os.getenv("MILVUS_URI"),
                "token": os.getenv("MILVUS_API_KEY")
            },
            primary_field="article_id",
            vector_field="content_embedding",
            text_field="content",
            drop_old=False
        )
        retriever = milvus_store.as_retriever()
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

        self._rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

    def generate_answer(self, content: str, prompt_template: Optional[str] = None) -> str:
        return self._rag_chain.invoke(
            f"다음과 같은 프롬프트에 맞춰서 답변해야합니다:'{prompt_template}' 그리고\n내용: {content} 에 대한 답변을 작성해주세요."
        )
    
    def close(self):
        self._client.close()

if __name__ == "__main__":
    service = LlmService()
    print(service.generate_answer("코닉오토메이션에 대해서 알려주세요."))