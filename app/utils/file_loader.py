"""
Common utilities for RAG search methods
"""

import os
import glob

from app.utils.logger import logger
from app.utils.text_utils import compute_file_hash


def read_docs(path: str):
    """Read all documents from data directory"""
    docs = []
    doc_paths = []
    deep_search = os.path.join(path, "**", "*.txt.clean")
    files = glob.glob(deep_search, recursive=True)
    for file_path in files:
        file_name = os.path.basename(file_path)
        current_document = {
            "id": str(file_path),
            "title": str(file_name),  # ToDo: Replace with the actual title if not exist use LLMs to generate one
            "content": "",
            "metadata": {
                "file_name": str(file_name),
                "file_path": str(file_path),
                "hash": "",
            },
        }
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:  # Only add non-empty files
                    current_document["content"] = content
                    current_document["metadata"]["hash"] = compute_file_hash(file_path)
                    docs.append(current_document)
                    doc_paths.append(file_path)
        except Exception as e:
            logger.warning(f"Warning: Could not read {file_path}: {e}")

    return docs, doc_paths


def get_doc_info(path):
    """Get document information for display"""
    docs, paths = read_docs(path)
    print(f"📚 Loaded {len(docs)} documents")
    print("\nDocuments:")
    for i, (doc, path) in enumerate(zip(docs, paths)):
        # Get relative path for cleaner display
        rel_path = path.replace("./app", "./")
        print(f"{i + 1}. [{rel_path}] {doc[:80]}{'...' if len(doc) > 80 else ''}")

    return docs, paths


if __name__ == "__main__":
    pass
    # from app.services.embedding_service import load_documents
    # articles = load_documents("../data/articles")
    # print(articles)
    # docs, paths = get_doc_info("../data/**/*.txt.clean")
    # print(paths)
