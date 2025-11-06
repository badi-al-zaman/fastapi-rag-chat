import chromadb
from chromadb.config import Settings

from app.core.config import settings as server_settings
from app.services.embedding_service import load_and_chunk_documents, setup_vector_database, process_user_query


# ========================================
# SECTION 4: VECTOR SEARCH
# ========================================

def search_vector_database(collection, query_embedding, top_k: int = 3):
    """
    Search vector database for relevant document chunks.

    This section demonstrates:
    - Vector similarity search
    - Result ranking and filtering
    - Similarity scoring
    - Top-k result selection
    """
    # Perform vector search
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k,  # How many results are returned?
    )

    # Process and display results
    search_results = []
    for i, (doc_id, distance, content, metadata) in enumerate(
            zip(
                results["ids"][0],
                results["distances"][0],
                results["documents"][0],
                results["metadatas"][0],
            )
    ):
        similarity = 1 - distance  # Convert distance to similarity
        search_results.append(
            {
                "id": doc_id,
                "content": content,
                "metadata": metadata,
                "similarity": similarity,
            }
        )

    return search_results


def search_query_pipline(query: str):
    # Initialize ChromaDB client
    chroma_client = chromadb.PersistentClient("vector_db/chroma", settings=Settings(anonymized_telemetry=False))

    # Create collection (what is the collection name? | What similarity metric is used? | embedding_functions)
    collection = chroma_client.get_or_create_collection(name="wiki_articles_v1", metadata={
        "hnsw:space": "cosine"}, )

    # index documents if they are not indexed before
    if collection.count() == 0:
        # Step 1: Load and chunk documents to the vector client
        chunks = load_and_chunk_documents(server_settings.DATA_DIR)

        # Step 2: Setup vector database client
        _ = setup_vector_database(chunks)

    # Step 3: Process user query
    _, query_embedding = process_user_query(query)

    # Step 4: Search vector database
    search_results = search_vector_database(collection, query_embedding, top_k=3)
    return search_results
