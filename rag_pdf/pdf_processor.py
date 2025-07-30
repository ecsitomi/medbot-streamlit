# =============================================================================
# rag_pdf/pdf_processor.py
# =============================================================================
"""
PDF feldolgozás és text chunking LangChain segítségével
"""
import os
from typing import List, Dict, Any
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import streamlit as st
from .config import RAG_CONFIG

class PDFProcessor:
    """PDF fájlok feldolgozása és chunkolása"""
    
    def __init__(self):
        self.pdf_dir = Path(RAG_CONFIG["paths"]["pdf_dir"])
        self.chunk_size = RAG_CONFIG["embedding"]["chunk_size"]
        self.chunk_overlap = RAG_CONFIG["embedding"]["chunk_overlap"]
        
        # Text splitter inicializálása
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_all_pdfs(self) -> List[Document]:
        """Összes PDF betöltése a medline_data/pdfs mappából"""
        documents = []
        
        if not self.pdf_dir.exists():
            st.warning(f"PDF mappa nem található: {self.pdf_dir}")
            return documents
        
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            st.warning("Nincsenek PDF fájlok a mappában")
            return documents
        
        for pdf_file in pdf_files:
            try:
                st.info(f"PDF feldolgozása: {pdf_file.name}")
                
                # PDF betöltése
                loader = PyPDFLoader(str(pdf_file))
                pdf_documents = loader.load()
                
                # Metadata hozzáadása
                for doc in pdf_documents:
                    doc.metadata["source"] = pdf_file.name
                    doc.metadata["file_path"] = str(pdf_file)
                
                documents.extend(pdf_documents)
                
            except Exception as e:
                st.error(f"Hiba a PDF feldolgozásnál ({pdf_file.name}): {e}")
                continue
        
        st.success(f"Összesen {len(documents)} oldal betöltve {len(pdf_files)} PDF fájlból")
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Dokumentumok feldarabolása kisebb chunk-okra"""
        if not documents:
            return []
        
        chunks = self.text_splitter.split_documents(documents)
        st.info(f"Összesen {len(chunks)} chunk létrehozva")
        
        # Chunk-ok tisztítása
        for chunk in chunks:
            # Üres sorok eltávolítása
            chunk.page_content = "\n".join(
                line for line in chunk.page_content.split("\n") 
                if line.strip()
            )
        
        return chunks
    
    def process_pdfs(self) -> List[Document]:
        """Teljes PDF feldolgozási folyamat"""
        # PDF-ek betöltése
        documents = self.load_all_pdfs()
        
        if not documents:
            return []
        
        # Chunkolás
        chunks = self.chunk_documents(documents)
        
        return chunks