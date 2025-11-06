from typing import List, Dict

import chromadb
from chromadb.config import Settings

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.file_loader import read_docs

from app.utils.logger import logger


# ========================================
# SECTION 1: DOCUMENT LOADING & CHUNKING
# ========================================

def load_and_chunk_documents(path: str):
    """
    Load sample documents and chunk them for better retrieval.
    This section demonstrates:
    - Documents loading
    - Text chunking using LangChain
    - Chunk size and overlap configuration
    """
    wiki_articles, _ = read_docs(path)

    # Configure text splitter from langchain
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,  # What is the chunk size?
        chunk_overlap=50,  # What is the overlap?
        length_function=len,
        # separators=["\n\n", "\n", " ", ""], # default values
    )

    # Chunk all documents
    all_chunks = []
    for doc in wiki_articles:
        chunks = text_splitter.split_text(doc["content"])
        for i, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "id": f"{doc['id']}_chunk_{i}",
                    "content": chunk,
                    "title": doc["title"],
                    "source_hash": doc["metadata"]["hash"],
                    "source_doc": doc["metadata"]["file_name"],
                    "source_path": doc["metadata"]["file_path"],
                }
            )
    return all_chunks


# ========================================
# SECTION 2: VECTOR DATABASE SETUP
# ========================================

def setup_vector_database(chunks: List[Dict]):
    """
    Set up ChromaDB vector database and store document chunks.

    This section demonstrates:
    - ChromaDB client initialization
    - Collection creation
    - Document embedding and storage
    - Vector database configuration
    """
    # Initialize ChromaDB client
    chroma_client = chromadb.PersistentClient("vector_db/chroma", settings=Settings(anonymized_telemetry=False))

    # Create collection (what is the collection name? | What similarity metric is used? | embedding_functions)
    collection = chroma_client.get_or_create_collection(name="wiki_articles_v1", metadata={
        "hnsw:space": "cosine"}, )

    # Add documents to collection (embeddings will be generated automatically)
    ids = []
    documents = []
    metadatas = []
    for chunk in chunks:
        # Prepare data for storage
        ids.append(chunk["id"])
        documents.append(chunk["content"])
        metadatas.append({
            "title": chunk["title"],
            "source": chunk["source_doc"],  # the parent file name
            "hash": chunk["source_hash"],  # the parent file hash
        })
    try:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    except Exception as e:
        logger.error(f"Failed to insert chunks: {str(e)}")
        raise
    return collection


# ========================================
# SECTION 3: QUERY PROCESSING
# ========================================
from sentence_transformers import SentenceTransformer


def process_user_query(query: str):
    """
    Process user query and convert to embedding for vector search.

    This section demonstrates:
    - Query preprocessing
    - Embedding model usage
    - Vector conversion
    - Query optimization
    """
    # Load embedding model (what model is used?)
    model = SentenceTransformer("all-MiniLM-L6-v2")  # What embedding model is used? same as chroma vector store

    # Preprocess query
    cleaned_query = query.lower().strip()

    # Convert query to embedding
    query_embedding = model.encode([cleaned_query])

    return model, query_embedding[0]
