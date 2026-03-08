import os
from abc import ABC, abstractmethod

class BaseRAGAdapter(ABC):
    @abstractmethod
    def retrieve_context(self, query: str, limit: int = 5) -> str:
        pass

class PGVectorAdapter(BaseRAGAdapter):
    def __init__(self):
        from core.db import get_connection
        self.get_connection = get_connection
        
    def retrieve_context(self, query: str, limit: int = 5) -> str:
        # Aquí se realizaría la llamada al embedding model local y el join con `memoria_vectorial` usando <=> (pgvector).
        # Por ahora mockeamos la respuesta.
        print(f"Buscando en PGVector RAG: {query}")
        return f"[PGVector Contexto Recuperado para: {query}]"

class NotebookLMEnterpriseAdapter(BaseRAGAdapter):
    def __init__(self):
        self.endpoint = os.getenv("NOTEBOOK_LM_ENDPOINT", "https://api.notebooklm.google.com/v1/query")
        self.api_key = os.getenv("NOTEBOOK_LM_API_KEY")
        
    def retrieve_context(self, query: str, limit: int = 5) -> str:
        if not self.api_key:
            return "[Error: NotebookLM API Key no configurada]"
            
        print(f"Haciendo fetch a NotebookLM Enterprise: {query}")
        # Cuando exista la API oficial, aquí se realizará el POST HTTP
        # import requests
        # res = requests.post(self.endpoint, json={"query": query}, headers={"Authorization": f"Bearer {self.api_key}"})
        # return res.json().get('context')
        return f"[NotebookLM Contexto Recuperado para: {query}]"

def get_rag_service() -> BaseRAGAdapter:
    engine = os.getenv("RAG_ENGINE", "pgvector").lower()
    if engine == "notebooklm":
        return NotebookLMEnterpriseAdapter()
    return PGVectorAdapter()

# Proxy Service (Facade) para consumo rápido en los agentes
def consultar_rag(query: str, limit: int = 5) -> str:
    service = get_rag_service()
    return service.retrieve_context(query, limit)
