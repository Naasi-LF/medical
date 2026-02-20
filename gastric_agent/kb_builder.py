from __future__ import annotations

import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from .config import get_config


def load_raw_docs(jsonl_path: str) -> list[Document]:
    path = Path(jsonl_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw document file not found: {jsonl_path}")

    docs: list[Document] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            content = (record.get("content") or "").strip()
            if not content:
                continue
            metadata = {
                "source": record.get("url", ""),
                "title": record.get("title", ""),
            }
            docs.append(Document(page_content=content, metadata=metadata))
    return docs


def build_vector_db(
    jsonl_path: str,
    persist_dir: str,
    chunk_size: int = 700,
    chunk_overlap: int = 64,
) -> int:
    config = get_config()
    raw_docs = load_raw_docs(jsonl_path)
    if not raw_docs:
        raise ValueError("No valid documents found in raw data file.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            "。",
            "；",
            "！",
            "？",
            ". ",
            "; ",
            "! ",
            "? ",
            "，",
            ", ",
            " ",
        ],
        length_function=len,
    )
    chunks = splitter.split_documents(raw_docs)
    if not chunks:
        raise ValueError("Text splitter produced no chunks.")

    embeddings = OpenAIEmbeddings(
        model=config.dashscope_embedding_model,
        api_key=config.dashscope_api_key,
        base_url=config.dashscope_base_url,
        check_embedding_ctx_length=False,
        chunk_size=10,
    )

    persist_path = Path(persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(persist_path),
        collection_name="gastric_knowledge",
    )
    return len(chunks)
