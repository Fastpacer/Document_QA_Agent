#!/usr/bin/env python3
"""
Script to clear existing vector data and re-process documents with new embeddings
"""

import os
import sys
from vector_store import VectorStore
from document_processor import DocumentProcessor
from config import Config

def reset_and_reprocess():
    """Clear vector store and re-process all documents"""
    print("🚀 Starting document re-processing with new embeddings...")
    
    # Initialize vector store with the new model
    vector_store = VectorStore(
        persist_directory=Config.VECTOR_DB_DIR,
        embedding_model=Config.EMBEDDING_MODEL
    )
    
    # Clear all existing data
    print("🧹 Clearing existing vector data...")
    try:
        vector_store.collection.delete(where={})
        print("✓ Vector store cleared successfully")
    except Exception as e:
        print(f"Error clearing vector store: {e}")
    
    # Process all documents in the upload directory
    processor = DocumentProcessor()
    upload_dir = Config.UPLOAD_DIR
    
    if not os.path.exists(upload_dir):
        print(f"Upload directory {upload_dir} does not exist")
        return
    
    processed_count = 0
    for filename in os.listdir(upload_dir):
        if filename.endswith('.pdf'):
            file_path = os.path.join(upload_dir, filename)
            print(f"📄 Processing {filename}...")
            
            try:
                # Extract text from PDF
                documents = processor.extract_text_from_pdf(file_path)
                
                # Add to vector store with new embeddings
                vector_store.add_documents(documents, filename)
                
                processed_count += 1
                print(f"✓ Successfully processed {filename}")
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
    
    print(f"\n🎉 Finished! Processed {processed_count} documents with {Config.EMBEDDING_MODEL} embeddings")

if __name__ == "__main__":
    reset_and_reprocess()