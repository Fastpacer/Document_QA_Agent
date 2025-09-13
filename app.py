from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from typing import List, Optional

from document_processor import DocumentProcessor
from vector_store import VectorStore
from query_processor import QueryProcessor
from arxiv_integration import ArxivIntegration
from config import Config

app = FastAPI(title="Document Q&A AI Agent")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components and ensure directories exist
Config.ensure_directories_exist()
processor = DocumentProcessor()
vector_store = VectorStore(persist_directory=Config.VECTOR_DB_DIR)
query_processor = QueryProcessor()
arxiv_client = ArxivIntegration()

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a PDF document"""
    try:
        # Ensure upload directory exists
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        file_path = os.path.join(Config.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process document
        documents = processor.extract_text_from_pdf(file_path)
        
        # Add to vector store
        vector_store.add_documents(documents, file.filename)
        
        return JSONResponse({
            "message": "Document processed successfully",
            "chunks": len(documents),
            "filename": file.filename
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/query")
async def query_document(query: str):
    """Query the document"""
    try:
        # Check if this is an Arxiv search request
        if query_processor.detect_arxiv_request(query):
            arxiv_results = arxiv_client.process_arxiv_query(query)
            return JSONResponse({
                "type": "arxiv_search",
                "response": arxiv_results["response"],
                "papers": arxiv_results["papers"],
                "suggested_action": "Use /arxiv-download endpoint to download any paper"
            })
        
        # Regular document query
        # Search for relevant context
        context = vector_store.search(query)
        
        if not context:
            return JSONResponse({
                "type": "no_context",
                "response": "I couldn't find relevant information in the uploaded documents. Would you like me to search for research papers on Arxiv instead?",
                "suggestion": "Try using /arxiv-search endpoint or rephrase your query."
            })
        
        # Process query
        answer = query_processor.process_query(query, context)
        
        return JSONResponse({
            "type": "document_answer",
            "answer": answer,
            "context_sources": [f"{doc['metadata']['source']} (page {doc['metadata']['page']})" for doc in context]
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/summarize")
async def summarize_document(filename: str = Query(..., description="Filename to summarize")):
    """Generate document summary for a specific file"""
    try:
        # Use the enhanced search that filters by source document
        context = vector_store.search_within_document("summary", filename, n_results=20)
        
        if not context:
            # If no specific document found, check if the file exists but hasn't been processed
            file_path = os.path.join(Config.UPLOAD_DIR, filename)
            if os.path.exists(file_path):
                return JSONResponse({
                    "error": f"File '{filename}' exists but hasn't been processed. Please upload it first.",
                    "suggestion": f"Use POST /upload endpoint with the file"
                })
            else:
                return JSONResponse({
                    "error": f"File '{filename}' not found.",
                    "suggestion": "Check the filename or use GET /documents to list available files"
                })
        
        # Generate summary
        summary = query_processor.summarize_document(context)
        
        return JSONResponse({
            "summary": summary,
            "filename": filename,
            "chunks_used": len(context),
            "document_pages": f"{min([c['metadata']['page'] for c in context])}-{max([c['metadata']['page'] for c in context])}"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.get("/arxiv-search")
async def arxiv_search(
    query: str = Query(..., description="Search query for Arxiv papers"),
    max_results: int = Query(5, description="Maximum number of results to return")
):
    """Search for papers on Arxiv"""
    try:
        results = arxiv_client.search_papers(query, max_results)
        
        if not results:
            return JSONResponse({
                "message": "No papers found for the given query",
                "query": query,
                "papers": []
            })
        
        return JSONResponse({
            "message": f"Found {len(results)} papers for '{query}'",
            "query": query,
            "papers": results
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching Arxiv: {str(e)}")

@app.post("/arxiv-download")
async def arxiv_download(
    arxiv_id: str = Query(..., description="Arxiv ID of the paper to download (e.g., 1706.03762)"),
    filename: Optional[str] = Query(None, description="Optional custom filename for the downloaded PDF")
):
    """Download a paper from Arxiv and automatically process it"""
    try:
        download_path = arxiv_client.download_paper(arxiv_id, filename)
        
        if download_path:
            # Process the downloaded paper
            documents = processor.extract_text_from_pdf(download_path)
            vector_store.add_documents(documents, os.path.basename(download_path))
            
            return JSONResponse({
                "message": "Paper downloaded and processed successfully",
                "arxiv_id": arxiv_id,
                "filename": os.path.basename(download_path),
                "chunks_processed": len(documents),
                "next_step": "You can now query this paper using the /query endpoint"
            })
        else:
            raise HTTPException(status_code=404, detail="Paper not found or download failed")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading paper: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List all processed documents with their chunk counts"""
    try:
        # Get unique documents from the vector store with more details
        processed_docs = {}
        
        collection_data = vector_store.collection.get()
        if collection_data['metadatas']:
            for i, metadata in enumerate(collection_data['metadatas']):
                source = metadata.get('source', 'unknown')
                if source not in processed_docs:
                    processed_docs[source] = {
                        "chunks": 0,
                        "pages": set(),
                        "content_length": 0
                    }
                processed_docs[source]["chunks"] += 1
                processed_docs[source]["pages"].add(metadata.get('page', 0))
                if i < len(collection_data['documents']):
                    processed_docs[source]["content_length"] += len(collection_data['documents'][i])
        
        # Format the response
        formatted_docs = []
        for name, data in processed_docs.items():
            formatted_docs.append({
                "filename": name,
                "chunks": data["chunks"],
                "pages": f"{min(data['pages'])}-{max(data['pages'])}" if data['pages'] else "N/A",
                "content_length": data["content_length"]
            })
        
        # Also check the upload directory for files that might not be processed yet
        uploaded_files = []
        if os.path.exists(Config.UPLOAD_DIR):
            uploaded_files = [f for f in os.listdir(Config.UPLOAD_DIR) if f.endswith('.pdf')]
        
        return JSONResponse({
            "processed_documents": formatted_docs,
            "uploaded_but_unprocessed": [
                f for f in uploaded_files if f not in processed_docs
            ],
            "total_processed": len(processed_docs),
            "total_chunks": sum([doc["chunks"] for doc in formatted_docs])
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.post("/query-document")
async def query_specific_document(query: str, filename: str = Query(..., description="Filename to query")):
    """Query a specific document"""
    try:
        # Search within the specific document
        context = vector_store.search_within_document(query, filename, n_results=10)
        
        if not context:
            return JSONResponse({
                "type": "no_context",
                "response": f"I couldn't find relevant information in '{filename}'.",
                "suggestion": "Try rephrasing your query or selecting a different document."
            })
        
        # Process query
        answer = query_processor.process_query(query, context)
        
        return JSONResponse({
            "type": "document_answer",
            "answer": answer,
            "filename": filename,
            "context_sources": [f"{doc['metadata']['source']} (page {doc['metadata']['page']})" for doc in context]
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.delete("/delete-document")
async def delete_document(filename: str = Query(..., description="Filename to delete")):
    """Delete a document and its vector data"""
    try:
        # Delete from vector store
        vector_deleted = vector_store.delete_document(filename)
        
        # Delete from file system
        file_path = os.path.join(Config.UPLOAD_DIR, filename)
        file_deleted = False
        if os.path.exists(file_path):
            os.remove(file_path)
            file_deleted = True
        
        return JSONResponse({
            "message": "Document deleted successfully",
            "vector_data_deleted": vector_deleted,
            "file_deleted": file_deleted,
            "filename": filename
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


    
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "Document Q&A AI Agent",
        "vector_db_connected": True,  # Simplified check
        "groq_api_available": bool(Config.GROQ_API_KEY)
    })

@app.get("/")
async def root():
    return {
        "message": "Document Q&A AI Agent API",
        "endpoints": {
            "POST /upload": "Upload and process PDF document",
            "POST /query": "Query processed documents",
            "POST /summarize": "Generate document summary",
            "GET /arxiv-search": "Search for papers on Arxiv",
            "POST /arxiv-download": "Download and process paper from Arxiv",
            "GET /documents": "List processed documents",
            "GET /health": "Health check"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)