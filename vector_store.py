import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import os

class VectorStore:
    def __init__(self, persist_directory: str = "data/vector_db"):
        # Use the new ChromaDB client initialization
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        self.collection = self.client.get_or_create_collection("documents")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def add_documents(self, documents: List[Dict], document_id: str):
        """Add documents to vector store"""
        texts = [doc["content"] for doc in documents]
        embeddings = self.embedding_model.encode(texts).tolist()
        metadatas = [{"page": doc["page"], "source": doc["source"]} for doc in documents]
        ids = [f"{document_id}_{i}" for i in range(len(documents))]
        
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar documents"""
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        return [
            {
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": results["distances"][0][i] if results["distances"] else 0
            }
            for i in range(len(results["documents"][0]))
        ]
    
    def search_within_document(self, query: str, source: str, n_results: int = 10) -> List[Dict]:
        """Search for similar documents within a specific source document"""
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where={"source": source}  # Filter by source document
        )
        
        return [
            {
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": results["distances"][0][i] if results["distances"] else 0
            }
            for i in range(len(results["documents"][0]))
        ]
    
    def get_document_chunks(self, source: str) -> List[Dict]:
        """Get all chunks from a specific document"""
        try:
            results = self.collection.get(
                where={"source": source}
            )
            
            return [
                {
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "id": results["ids"][i]
                }
                for i in range(len(results["documents"]))
            ]
        except Exception as e:
            print(f"Error getting document chunks: {e}")
            return []

    def delete_document(self, source: str):
        """Delete all chunks of a specific document"""
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"source": source}
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                print(f"✓ Deleted {len(results['ids'])} chunks for document: {source}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    def get_collection_info(self):
        """Get information about the collection"""
        try:
            count = self.collection.count()
            return {
                "count": count,
                "name": self.collection.name
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {"count": 0, "name": "unknown"}