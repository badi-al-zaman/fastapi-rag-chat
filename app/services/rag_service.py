from app.services.embedding_service import get_index
from llama_index.llms.ollama import Ollama


def run_complete_rag_pipeline_v2(query: str):
    """
    Run the complete RAG pipeline from start to finish.
    This demonstrates the full flow:
    1. load prebuilt vector database (index)
    2. used as a query engin
    3. Response generation
    """
    index = get_index()
    model = Ollama(
        model="llama3.1:8b",  # local model name
        request_timeout=360.0,
        # Manually set the context window to limit memory usage
        context_window=8000,
    )
    retriever = index.as_query_engine(llm=model, similarity_top_k=3)
    return retriever.query(query)
