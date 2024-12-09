from typing import Any
from diskcache import FanoutCache
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from mm_llm.config import settings 


async def generate_chunk_context(
    whole_document: str, 
    chunk_content: str,
    model: ChatOpenAI 
) -> str:
    prompt = f"""
<document>
{whole_document}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{chunk_content}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else.

please answer in korean."""
    response = await model.ainvoke(prompt, max_tokens=5_000, temperature=0.5)
    print(response)

    # Assuming response.content is a list, join the strings if they are present
    if isinstance(response.content, list):
        content = ''.join(
            item if isinstance(item, str) else '' for item in response.content
        )
    else:
        content = response.content
    return content.strip()

model = ChatOpenAI(model="gpt-4o-mini")
embeddings = OpenAIEmbeddings(model=settings.DEFAULT_EMBEDDING_MODEL)
cache_process_chunk = FanoutCache(
    directory=".cache/process_chunk",
    timeout=1,
    shards=64,
    size_limit=10e9,
    eviction_policy="least-recently-used",
) # key: {whole_document}_{chunk_contents} value: (enhanced_chunk, enhanced_embeddings) 
def process_chunk(
    whole_document: str,
    chunk_contents: str,
) -> tuple[str, list[float]] | Any:
    cached_result = cache_process_chunk.get(whole_document)
    if cached_result is not None:
        return cached_result
    
    context = generate_chunk_context(whole_document, chunk_content, model)
    enhanced_chunk = f"""
<context>
{context} 
</context>

<chunk>
{chunk_content}
</chunk>"""
    enhanced_embeddings = await embeddings.aembed_query(enhanced_chunk)
    cache_process_chunk.set(whole_document, (enhanced_chunk, enhanced_embeddings))
    return enhanced_chunk, enhanced_embeddings 