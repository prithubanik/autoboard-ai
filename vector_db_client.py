import os
from typing import List, Dict, Any

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

os.makedirs("database/chroma_storage", exist_ok=True)

embedder = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

vector_db = Chroma(
    collection_name="chart_memory",
    embedding_function=embedder,
    persist_directory="./database/chroma_storage"
)

def get_collection():
    return vector_db

def add_chart_memory(session_id: str, chart_index: int, payload: Dict[str, Any]) -> None:
    doc = Document(
        page_content=str(payload),
        metadata={
            "session_id": session_id,
            "chart_index": chart_index,
            "chart_type": payload.get("chart_type"),
            "variables_used": ",".join(payload.get("variables_used", [])),
            "business_question": payload.get("business_question", ""),
            "signature": payload.get("chart_signature", ""),
            "takeaway": payload.get("takeaway", ""),
        },
        id=f"{session_id}-chart-{chart_index}"
    )
    vector_db.add_documents([doc])

def search_similar_charts(session_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
    results = vector_db.similarity_search_with_score(query, k=k, filter={"session_id": session_id})
    output = []
    for doc, score in results:
        output.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": score,
        })
    return output