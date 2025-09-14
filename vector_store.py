import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import os
import time

class VectorStore:
    def __init__(self, persist_directory: str = "data/vector_db", embedding_model: str = "mpnet"):
        # Use the new ChromaDB client initialization
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        self.collection = self.client.get_or_create_collection("documents")
        self.embedding_model = self._get_embedding_model(embedding_model)
        print(f"✓ Loaded embedding model: {type(self.embedding_model).__name__}")
    
    def _get_embedding_model(self, model_type: str):
        """Get the appropriate embedding model based on configuration"""
        # Ordered by quality (best first)
        model_priority_list = [
            "sentence-transformers/all-mpnet-base-v2",  # Best overall
            "mixedbread-ai/mxbai-embed-large-v1",       # Excellent alternative
            "thenlper/gte-base",                        # Good general purpose
            "sentence-transformers/all-MiniLM-L6-v2"    # Basic fallback
        ]
        
        model_map = {
            "default": "sentence-transformers/all-mpnet-base-v2",
            "mpnet": "sentence-transformers/all-mpnet-base-v2",
            "mxbai": "mixedbread-ai/mxbai-embed-large-v1",
            "gte": "thenlper/gte-base",
            "minilm": "sentence-transformers/all-MiniLM-L6-v2"
        }
        
        # Get the requested model name
        model_name = model_map.get(model_type, model_map["default"])
        
        # Try the requested model first, then fall back through the priority list
        models_to_try = [model_name] + model_priority_list
        
        for model in models_to_try:
            try:
                print(f"Attempting to load embedding model: {model}")
                start_time = time.time()
                model_instance = SentenceTransformer(model)
                load_time = time.time() - start_time
                print(f"✓ Successfully loaded {model} in {load_time:.2f} seconds")
                return model_instance
            except Exception as e:
                print(f"Failed to load {model}: {e}")
                continue
        
        # If all else fails, use a basic model that should always work
        print("All embedding models failed, using ChromaDB's default embeddings")
        return None
    
    def add_documents(self, documents: List[Dict], document_id: str):
        """Add documents to vector store with progress tracking"""
        texts = [doc["content"] for doc in documents]
        metadatas = [{"page": doc["page"], "source": doc["source"]} for doc in documents]
        ids = [f"{document_id}_{i}" for i in range(len(documents))]
        
        # Use custom embeddings if we have a model, otherwise use ChromaDB's default
        if self.embedding_model is not None:
            print(f"Generating embeddings for {len(texts)} chunks using {type(self.embedding_model).__name__}...")
            start_time = time.time()
            
            try:
                embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
                embed_time = time.time() - start_time
                print(f"✓ Embeddings generated in {embed_time:.2f} seconds")
                
                self.collection.add(
                    embeddings=embeddings.tolist(),
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                print(f"✓ Added {len(documents)} chunks from {document_id} with custom embeddings")
                return
                
            except Exception as e:
                print(f"Error generating custom embeddings: {e}")
                print("Falling back to ChromaDB's default embeddings")
        
        # Fallback: use ChromaDB's default embeddings
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✓ Added {len(documents)} chunks using ChromaDB's default embeddings")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar documents with enhanced query processing"""
        try:
            # Preprocess query for better results
            processed_query = self._preprocess_query(query)
            
            # Use custom embeddings if available
            if self.embedding_model is not None:
                query_embedding = self.embedding_model.encode([processed_query]).tolist()
                results = self.collection.query(
                    query_embeddings=query_embedding,
                    n_results=n_results
                )
            else:
                # Fallback to text-based search
                results = self.collection.query(
                    query_texts=[processed_query],
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
        except Exception as e:
            print(f"Error in search: {e}")
            # Fallback to text-based search if embedding fails
            return self._fallback_text_search(query, n_results)
    
    def search_within_document(self, query: str, source: str, n_results: int = 10) -> List[Dict]:
        """Search for similar documents within a specific source document"""
        try:
            # Preprocess query for better results
            processed_query = self._preprocess_query(query)
            
            # Use custom embeddings if available
            if self.embedding_model is not None:
                query_embedding = self.embedding_model.encode([processed_query]).tolist()
                results = self.collection.query(
                    query_embeddings=query_embedding,
                    n_results=n_results,
                    where={"source": source}
                )
            else:
                # Fallback to text-based search
                results = self.collection.query(
                    query_texts=[processed_query],
                    n_results=n_results,
                    where={"source": source}
                )
            
            return [
                {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": results["distances"][0][i] if results["distances"] else 0
                }
                for i in range(len(results["documents"][0]))
            ]
        except Exception as e:
            print(f"Error in search_within_document: {e}")
            # Fallback to text-based search if embedding fails
            return self._fallback_text_search_within_document(query, source, n_results)
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query to improve search results"""
        # Expand technical abbreviations
        technical_expansions = {
            "ai": "artificial intelligence",
            "ml": "machine learning",
            "nlp": "natural language processing",
            "cv": "computer vision",
            "llm": "large language model",
            "framework": "framework methodology approach",
            "verification": "verification validation testing",
            "bregman": "bregman divergence loss function",
            "squared": "squared error loss function"
        }
        
        processed_query = query.lower()
        for short, long in technical_expansions.items():
            if short in processed_query:
                processed_query = processed_query.replace(short, f"{short} {long}")
        
        return processed_query
    
    def _fallback_text_search(self, query: str, n_results: int) -> List[Dict]:
        """Fallback search method if embedding search fails"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            return [
                {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 0  # No distance score available
                }
                for i in range(len(results["documents"][0]))
            ]
        except Exception as e:
            print(f"Fallback search also failed: {e}")
            return []
    
    def _fallback_text_search_within_document(self, query: str, source: str, n_results: int) -> List[Dict]:
        """Fallback search method for within-document search if embedding fails"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"source": source}
            )
            
            return [
                {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 0  # No distance score available
                }
                for i in range(len(results["documents"][0]))
            ]
        except Exception as e:
            print(f"Fallback search within document also failed: {e}")
            return []
    
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
