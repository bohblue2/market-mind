from typing import List

from diskcache import FanoutCache
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel

from mm_llm.config import settings

CHUNK_CONTEXT_TEMPLATE = PromptTemplate(
    input_variables=["whole_document", "chunk_content"],
    template="""<document>
{whole_document}
</document>

Here is the chunk we want to situate within the whole document
<chunk>
{chunk_content}
</chunk>

Please give a short succinct context to situate this chunk within 
the overall document for the purposes of improving search retrieval 
of the chunk. Answer only with the succinct context and nothing else.

Please answer in korean."""
)

ENHANCED_CHUNK_PROMPT_TEMPLATE = PromptTemplate(
        input_variables=["context", "chunk_content"],
        template="""<context>
{context}
</context>

<chunk>
{chunk_content}
</chunk>"""
)

class ProecssedChunks(BaseModel):
    enhanced_chunks: list[str] 
    enhanced_embeddings: list[list[float]]

    def __str__(self) -> str:
        """Return a string representation of the processed chunks."""
        return f"ProecssedChunks(enhanced_chunk={self.enhanced_chunks}, enhanced_embedding={self.enhanced_embeddings})"

model = ChatOpenAI(model="gpt-4o-mini")
embeddings = OpenAIEmbeddings(model=settings.DEFAULT_EMBEDDING_MODEL)
cache_process_chunk = FanoutCache(
    directory=".cache/process_chunk",
    timeout=1,
    shards=64,
    size_limit=10e9,
    eviction_policy="least-recently-used",
)
def process_chunk(
    whole_document: str,
    chunk_contents: list[str],
    # TODO: Implement cache name for this function
) -> ProecssedChunks:
    # NOTE: This function is not async because it is called from a synchronous context
    cached_result = cache_process_chunk.get(f"{whole_document}_{chunk_contents}")
    if cached_result is not None:
        return cached_result # type: ignore

    chunk_contexts: List[str] = []
    chunk_contexts = [
        CHUNK_CONTEXT_TEMPLATE.format(whole_document=whole_document, chunk_content=chunk_content)
        for chunk_content in chunk_contents
    ]
    responses: list[AIMessage] = model.batch(
        chunk_contexts, # type: ignore
        config={"max_concurrency": 15},
        return_exceptions=False,
    )

    enhanced_chunks: list[str] = [
        ENHANCED_CHUNK_PROMPT_TEMPLATE.format(context=response.content, chunk_content=chunk_content) \
            for response, chunk_content in zip(responses, chunk_contents)] # type: ignore
    enhanced_embeddings: list[list[float]] = embeddings.embed_documents(enhanced_chunks) 
    ret = ProecssedChunks(enhanced_chunks=enhanced_chunks, enhanced_embeddings=enhanced_embeddings)
    cache_process_chunk.set(f"{whole_document}_{chunk_contents}", ret)
    return ret


if __name__ == "__main__":
    whole_document = "This is the whole document that we want to split into chunks"
    chunk_contents = [
        "This is the first chunk",
        "This is the second chunk",
        "This is the third chunk"
    ]
    ret = process_chunk(whole_document, chunk_contents)
    print(ret)
