import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredExcelLoader,
)
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config import cfg


CATEGORY_DIR_MAP = {
    "regulations": cfg.data.regulations_dir,
    "roadmaps"   : cfg.data.roadmaps_dir,
    "forecasts"  : cfg.data.forecasts_dir,
    "ecostuxure" : cfg.data.grid_platform_dir,
    "policies"   : cfg.data.policies_dir,
}

LOADER_MAP = {
    ".pdf" : PyPDFLoader,
    ".txt" : TextLoader,
    ".docx": Docx2txtLoader,
    ".csv" : CSVLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls" : UnstructuredExcelLoader,
}


def get_embeddings():
    return OllamaEmbeddings(
        model    = cfg.ollama.embedding,
        base_url = cfg.ollama.base_url,
    )


def load_file(filepath: str, category: str) -> list:
    ext        = os.path.splitext(filepath)[-1].lower()
    loader_cls = LOADER_MAP.get(ext)

    if not loader_cls:
        print(f"Skipping unsupported file: {filepath}")
        return []

    try:
        docs = loader_cls(filepath).load()
        for doc in docs:
            doc.metadata["category"] = category
            doc.metadata["source"]   = os.path.basename(filepath)
        print(f"Loaded [{category}] {os.path.basename(filepath)} ({len(docs)} pages)")
        return docs
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []


def load_all_documents() -> list:
    all_docs = []
    for category, folder in CATEGORY_DIR_MAP.items():
        if not os.path.exists(folder):
            print(f"Folder not found, skipping: {folder}")
            continue
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            docs     = load_file(filepath, category)
            all_docs.extend(docs)
    return all_docs


def load_single_file(filepath: str, category: str) -> list:
    return load_file(filepath, category)


def chunk_documents(docs: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = cfg.data.chunk_size,
        chunk_overlap = cfg.data.chunk_overlap,
        separators    = ["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(docs)
    print(f"Total chunks created: {len(chunks)}")
    return chunks


def store_in_chromadb(chunks: list):
    print(f"Loading embedding model: {cfg.ollama.embedding}")
    embeddings = get_embeddings()
    print(f"Storing {len(chunks)} chunks in ChromaDB...")
    Chroma.from_documents(
        documents         = chunks,
        embedding         = embeddings,
        collection_name   = cfg.chroma.collection_name,
        persist_directory = cfg.chroma.db_path,
    )
    print(f"Successfully stored {len(chunks)} chunks in ChromaDB.")


def ingest_all():
    print("=" * 60)
    print("Grid Decarbonisation RAG - Full Ingestion Pipeline")
    print("=" * 60)
    docs = load_all_documents()
    if not docs:
        print("No documents found. Add files to data/ folders.")
        return 0
    print(f"Total documents loaded: {len(docs)}")
    chunks = chunk_documents(docs)
    store_in_chromadb(chunks)
    print("Ingestion complete.")
    return len(chunks)


def ingest_single(filepath: str, category: str) -> int:
    print(f"Ingesting single file: {filepath} [{category}]")
    docs   = load_single_file(filepath, category)
    if not docs:
        return 0
    chunks = chunk_documents(docs)
    store_in_chromadb(chunks)
    return len(chunks)


if __name__ == "__main__":
    ingest_all()