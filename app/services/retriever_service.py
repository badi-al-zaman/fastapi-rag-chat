# ========================================
# Version 2 setup using llama-index framework
# ========================================
from app.services.embedding_service import get_index


def search_query_pipline_v2(query: str):
    # load embedded chunks from chroma -collection
    index = get_index()
    retriever = index.as_retriever(similarity_top_k=3)
    # Step 4: Search vector database
    response = retriever.retrieve(query)
    return response
