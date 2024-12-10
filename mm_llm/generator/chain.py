import os
from operator import itemgetter
from typing import Any, Dict, List

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (ChatPromptTemplate, MessagesPlaceholder)
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import (ConfigurableField, Runnable,
                                      RunnableBranch, RunnableLambda,
                                      RunnablePassthrough)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

from mm_llm.config import settings
from mm_llm.constant import DEFAULT_EMBEDDING_MODEL
from mm_llm.enums import RunNames
from mm_llm.models import ChatRequest
from mm_llm.prompts.default import REPHRASE_TEMPLATE, RESPONSE_TEMPLATE
from mm_llm.spliter import format_docs_with_ids
from langchain_postgres.vectorstores import PGVector

def get_retriever(
    embeddings: OpenAIEmbeddings = OpenAIEmbeddings(model=DEFAULT_EMBEDDING_MODEL),
    collection_name: str = "market_mind",
    connection: str = str(settings.SQLALCHEMY_DATABASE_URL)
) -> BaseRetriever:
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )
    return vector_store.as_retriever()
    

def create_retriever_chain(
    llm: LanguageModelLike, retriever: BaseRetriever
) -> Runnable:
    CONDENSE_QUESTION_PROMPT = REPHRASE_TEMPLATE
    condense_question_chain = (
        CONDENSE_QUESTION_PROMPT | llm | StrOutputParser()
    ).with_config(
        run_name=RunNames.CONDENSE_QUESTION.value,
    )
    conversation_chain = condense_question_chain | retriever

    return RunnableBranch(
        (
            RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
                run_name=RunNames.HAS_CHAT_HISTORY_CHECK.value
            ),
            conversation_chain.with_config(run_name=RunNames.RETRIEVAL_CHAIN_WITH_HISTORY.value),
        ),
        (
            RunnableLambda(itemgetter("question")).with_config(
                run_name=RunNames.ITEMGETTER_QUESTION.value
            )
            | retriever
        ).with_config(run_name=RunNames.RETRIEVAL_CHAIN_WITH_NO_HISTORY.value),
    ).with_config(run_name=RunNames.ROUTE_DEPENDING_ON_CHAT_HISTORY.value)


def serialize_history(request: Dict[str, Any]) -> List[BaseMessage]:
    chat_history = request.get("chat_history", [])
    converted_chat_history: List[BaseMessage] = []
    for message in chat_history:
        if message.get("human") is not None:
            converted_chat_history.append(HumanMessage(content=message["human"]))
        if message.get("ai") is not None:
            converted_chat_history.append(AIMessage(content=message["ai"]))
    return converted_chat_history

def create_chain(llm: LanguageModelLike, retriever: BaseRetriever) -> Runnable:
    retriever_chain = create_retriever_chain(
        llm,
        retriever,
    ).with_config(run_name="FindDocs")
    context = (
        RunnablePassthrough.assign(docs=retriever_chain)
        .assign(context=lambda x: format_docs_with_ids(x["docs"]))
        .with_config(run_name="RetrieveDocs")
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RESPONSE_TEMPLATE),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )
    default_response_synthesizer = prompt | llm

    response_synthesizer = (
        default_response_synthesizer.configurable_alternatives(
            ConfigurableField("llm"),
            default_key="openai_gpt4_o",
            anthropic_claude_3_haiku=default_response_synthesizer,
        )
        | StrOutputParser()
    ).with_config(run_name="GenerateResponse")
    return (
        RunnablePassthrough.assign(chat_history=serialize_history) # type: ignore 
        | context
        | response_synthesizer
    )

gpt4_o = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    streaming=True,
    api_key=SecretStr(settings.OPENAI_API_KEY),
)
claude_3_sonnet = ChatAnthropic(
    model_name="claude-3-5-sonnet-20240620",
    temperature=0,
    timeout=None,
    max_retries=2,
    stop=["\n"],
    api_key=SecretStr(os.environ.get("ANTHROPIC_API_KEY", "default")),
)

llm = gpt4_o.configurable_alternatives(
    ConfigurableField("llm"),
    default_key="openai_gpt4_o",
    antropic_claude_3_sonnet=claude_3_sonnet
).with_fallbacks(
    [gpt4_o, claude_3_sonnet]
)

retriever = get_retriever()
answer_chain = create_chain(llm, retriever)

if __name__ == "__main__":
    print(settings.OPENAI_API_KEY)
    answer_chain.invoke(ChatRequest(question="What is the capital of France?", chat_history=[{"human": "What is the capital of France?"}]).model_dump())