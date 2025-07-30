# =============================================================================
# rag_pdf/vector_store.py
# =============================================================================
"""
Chroma vector store kezelése
"""
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
import streamlit as st
import os
from .config import RAG_CONFIG

class VectorStoreManager:
    """Chroma vector store kezelése"""
    
    def __init__(self, openai_api_key: str):
        self.persist_directory = RAG_CONFIG["chroma"]["persist_directory"]
        self.collection_name = RAG_CONFIG["chroma"]["collection_name"]
        
        # OpenAI embeddings inicializálása
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            model=RAG_CONFIG["embedding"]["model"]
        )
        
        self.vectorstore = None
    
    def create_or_load_vectorstore(self, documents: List[Document] = None) -> Chroma:
        """Vector store létrehozása vagy betöltése"""
        
        # Ha már létezik a persist directory, próbáljuk betölteni
        if os.path.exists(self.persist_directory) and not documents:
            try:
                st.info("Meglévő vector store betöltése...")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
                st.success("Vector store sikeresen betöltve")
                return self.vectorstore
            except Exception as e:
                st.warning(f"Vector store betöltési hiba: {e}")
        
        # Új vector store létrehozása
        if documents:
            st.info("Új vector store létrehozása...")
            
            # Ha létezik, töröljük a régit
            if os.path.exists(self.persist_directory):
                import shutil
                shutil.rmtree(self.persist_directory)
            
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
                collection_name=self.collection_name
            )
            
            # Persist to disk
            self.vectorstore.persist()
            st.success("Vector store sikeresen létrehozva és mentve")
        
        return self.vectorstore
    
    def similarity_search(self, query: str, k: int = 5, 
                         score_threshold: float = 0.7) -> List[Document]:
        """Hasonlósági keresés a vector store-ban"""
        if not self.vectorstore:
            st.error("Vector store nincs inicializálva")
            return []
        
        try:
            # Keresés végrehajtása relevancia pontszámmal
            results = self.vectorstore.similarity_search_with_relevance_scores(
                query=query,
                k=k
            )
            
            # Szűrés relevancia alapján
            filtered_results = [
                doc for doc, score in results 
                if score >= score_threshold
            ]
            
            st.info(f"Találatok száma: {len(filtered_results)} (küszöb: {score_threshold})")
            
            return filtered_results
            
        except Exception as e:
            st.error(f"Keresési hiba: {e}")
            return []
    
    def search_by_symptoms(self, symptoms: List[str], 
                          diagnosis: str = None) -> List[Document]:
        """Keresés tünetek és diagnózis alapján"""
        # Keresési query összeállítása
        query_parts = []
        
        if symptoms:
            query_parts.append(f"Tünetek: {', '.join(symptoms)}")
        
        if diagnosis:
            query_parts.append(f"Diagnózis: {diagnosis}")
        
        query = " ".join(query_parts)
        
        # Keresés
        k = RAG_CONFIG["rag"]["top_k"]
        threshold = RAG_CONFIG["rag"]["score_threshold"]
        
        return self.similarity_search(query, k=k, score_threshold=threshold)