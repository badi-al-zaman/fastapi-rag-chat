# ========================================
# SECTION 7: COMPLETE RAG PIPELINE
# ========================================
from app.services.embedding_service import load_and_chunk_documents
from app.services.embedding_service import setup_vector_database, process_user_query
from app.services.retriever_service import search_vector_database
from app.services.generator_service import augment_prompt_with_context, generate_response
from app.core.config import settings as server_settings

DATA_DIR = server_settings.DATA_DIR


def run_complete_rag_pipeline(query: str):
    """
    Run the complete RAG pipeline from start to finish.

    This demonstrates the full flow:
    1. Document loading and chunking
    2. Vector database setup
    3. Query processing
    4. Vector search
    5. Context augmentation
    6. Response generation
    """
    # Step 1: Load and chunk documents
    chunks = load_and_chunk_documents(DATA_DIR)

    # Step 2: Setup vector database
    collection = setup_vector_database(chunks)

    # Step 3: Process user query
    _, query_embedding = process_user_query(query)

    # Step 4: Search vector database
    search_results = search_vector_database(collection, query_embedding, top_k=3)

    # Step 5: Augment prompt with context
    augmented_prompt = augment_prompt_with_context(query, search_results)

    # Step 6: Generate response
    response = generate_response(augmented_prompt)

    return response
