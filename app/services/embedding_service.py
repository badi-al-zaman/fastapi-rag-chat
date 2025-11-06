# ========================================
# Version 2 setup using llama-index framework
# ========================================
# from llama_index.core.extractors import TitleExtractor
# from llama_index.llms.ollama import Ollama
import chromadb
from chromadb.config import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.bridge.pydantic import BaseModel
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import SimpleDirectoryReader
from llama_index.core import VectorStoreIndex

from app.utils.logger import logger


class Title(BaseModel):
    """A Document Title """
    title: str


def load_and_chunk_documents_v2(vector_store, path: str):
    """
    Load sample documents and apply text transformations then chunks them for better retrieval.
    This section demonstrates:
    - Document loading from sample data
    - Text chunking using pipe ingestion of llama-index
    - Chunk size and overlap configuration
    - generate chunks embeddings & store them
    """

    # Load documents from directory
    documents = SimpleDirectoryReader(
        input_dir=path,
        filename_as_id=True
    ).load_data()

    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # configure LLM model to use it for extracting documents' metadata like: title,....
    # llm = Ollama(
    #     model="llama3.1:8b",  # local model name
    #     request_timeout=360.0,
    #     context_window=8000
    # )
    # sllm = llm.as_structured_llm(Title)

    # create the chunks' pipeline with transformations
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=200, chunk_overlap=50),
            # TitleExtractor(llm=sllm),
            embed_model,
        ],
        docstore=SimpleDocumentStore(),
        vector_store=vector_store,
    )

    # Load the docstore from disk at the start (if it exists) to check for duplicated docs
    try:
        pipeline.load(persist_dir="cache/pipeline_storage")
    except Exception as e:
        logger.warning(f"Failed to load pipeline from cache: {str(e)}")

    # run the pipeline to generate documents embeddings and store them
    nodes = pipeline.run(documents=documents, num_workers=4)

    # print(nodes[0].extra_info["document_title"])

    # save -- Local Cache Management --
    pipeline.persist("cache/pipeline_storage")


def setup_vector_database_v2():
    """
    Set up ChromaDB vector database and store document chunks.
    This section demonstrates:
    - ChromaDB client initialization
    - Collection creation
    - Vector database configuration
    """
    # Initialize ChromaDB client
    chroma_client = chromadb.PersistentClient("vector_db/chroma", settings=Settings(anonymized_telemetry=False))

    # Create collection (what is the collection name? | What similarity metric is used? | embedding_functions)
    chroma_collection = chroma_client.get_or_create_collection(name="wiki_articles_v2", metadata={
        "hnsw:space": "cosine"})

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    return vector_store


def get_index():
    # Step 1: Setup vector database
    vector_store = setup_vector_database_v2()

    # storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store, embed_model=HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2"),
    )
    return index
