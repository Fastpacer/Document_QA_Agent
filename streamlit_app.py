import streamlit as st
import requests
import json
import os
from typing import List, Dict, Optional

# Backend API URL
BACKEND_URL = "http://localhost:8000"

def main():
    st.set_page_config(
        page_title="Document Q&A AI Agent",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📄 Document Q&A AI Agent")
    st.markdown("Upload documents, ask questions, and search for research papers")
    
    # Initialize session state with all required variables
    if "processed_documents" not in st.session_state:
        st.session_state.processed_documents = []
    
    if "arxiv_results" not in st.session_state:
        st.session_state.arxiv_results = []
    
    if "selected_doc_query" not in st.session_state:
        st.session_state.selected_doc_query = None
    
    if "selected_doc_summarize" not in st.session_state:
        st.session_state.selected_doc_summarize = None
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio(
        "Go to",
        ["Upload Documents", "Query Documents", "Summarize Documents", "Research Paper Search", "Document Management"]
    )
    
    # Check if backend is running
    try:
        health_response = requests.get(f"{BACKEND_URL}/health")
        if health_response.status_code != 200:
            st.error("Backend server is not running. Please start the FastAPI server first.")
            st.stop()
    except:
        st.error("Cannot connect to backend server. Please make sure it's running on localhost:8000")
        st.stop()
    
    # Load processed documents
    load_documents()
    
    # App sections
    if app_mode == "Upload Documents":
        render_upload_section()
    elif app_mode == "Query Documents":
        render_query_section()
    elif app_mode == "Summarize Documents":
        render_summarize_section()
    elif app_mode == "Research Paper Search":
        render_research_section()
    elif app_mode == "Document Management":
        render_management_section()

def load_documents():
    """Load processed documents from backend"""
    try:
        docs_response = requests.get(f"{BACKEND_URL}/documents")
        if docs_response.status_code == 200:
            st.session_state.processed_documents = docs_response.json().get("processed_documents", [])
    except:
        st.session_state.processed_documents = []

def render_upload_section():
    st.header("📤 Upload Documents")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        st.write("Filename:", uploaded_file.name)
        
        if st.button("Upload and Process"):
            with st.spinner("Processing document..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = requests.post(f"{BACKEND_URL}/upload", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Document processed successfully! {result['chunks']} chunks added.")
                    
                    # Refresh document list
                    load_documents()
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

def render_query_section():
    st.header("❓ Query Documents")
    
    if not st.session_state.processed_documents:
        st.warning("No documents processed yet. Please upload documents first.")
        return
    
    # Document selection
    document_options = [doc["filename"] for doc in st.session_state.processed_documents]
    document_options.insert(0, "All Documents")  # Add option to search all documents
    
    selected_doc = st.selectbox(
        "Select document to query:",
        document_options,
        index=0,
        key="query_doc_select"
    )
    
    query = st.text_input("Enter your question:")
    
    if st.button("Ask Question") and query:
        with st.spinner("Searching for answers..."):
            if selected_doc == "All Documents":
                # Use the original query endpoint
                response = requests.post(f"{BACKEND_URL}/query", params={"query": query})
            else:
                # Use the new document-specific query endpoint
                response = requests.post(
                    f"{BACKEND_URL}/query-document", 
                    params={"query": query, "filename": selected_doc}
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result["type"] == "document_answer":
                    st.subheader("Answer:")
                    st.write(result["answer"])
                    
                    with st.expander("View Context Sources"):
                        for source in result["context_sources"]:
                            st.write(f"- {source}")
                
                elif result["type"] == "arxiv_search":
                    st.info(result["response"])
                    # Store arxiv results in session state
                    st.session_state.arxiv_results = result.get("papers", [])
                    
                    if st.session_state.arxiv_results:
                        st.subheader("Suggested Research Papers:")
                        for i, paper in enumerate(st.session_state.arxiv_results[:3], 1):
                            st.write(f"{i}. **{paper['title']}**")
                            st.write(f"   Authors: {', '.join(paper['authors'][:2])}")
                            st.write(f"   Published: {paper['published']}")
                            st.write(f"   [PDF Link]({paper['pdf_url']})")
                            st.write("---")
                
                elif result["type"] == "no_context":
                    st.warning(result["response"])
                    st.info(result["suggestion"])
            
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

def render_summarize_section():
    st.header("📝 Summarize Documents")
    
    if not st.session_state.processed_documents:
        st.warning("No documents processed yet. Please upload documents first.")
        return
    
    document_options = [doc["filename"] for doc in st.session_state.processed_documents]
    selected_doc = st.selectbox(
        "Select a document to summarize:", 
        document_options,
        key="summarize_doc_select"
    )
    
    if st.button("Generate Summary"):
        with st.spinner("Generating summary..."):
            response = requests.post(f"{BACKEND_URL}/summarize", params={"filename": selected_doc})
            
            if response.status_code == 200:
                result = response.json()
                
                if "summary" in result:
                    st.subheader(f"Summary of {selected_doc}:")
                    st.write(result["summary"])
                    
                    with st.expander("Summary Details"):
                        st.write(f"Chunks used: {result.get('chunks_used', 'N/A')}")
                        st.write(f"Pages: {result.get('document_pages', 'N/A')}")
                else:
                    st.error(result.get("error", "Unknown error"))
                    st.info(result.get("suggestion", ""))
            
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

def render_research_section():
    st.header("🔍 Research Paper Search")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        research_query = st.text_input("Search for research papers:")
        max_results = st.slider("Maximum results", 1, 10, 5)
    
    with col2:
        st.write("")
        st.write("")
        if st.button("Search Arxiv") and research_query:
            with st.spinner("Searching research papers..."):
                response = requests.get(
                    f"{BACKEND_URL}/arxiv-search", 
                    params={"query": research_query, "max_results": max_results}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Store results in session state
                    st.session_state.arxiv_results = result.get("papers", [])
                    
                    if not st.session_state.arxiv_results:
                        st.info("No papers found for your query.")
                    else:
                        st.success(f"Found {len(st.session_state.arxiv_results)} papers")
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
    
    # Display search results - check if arxiv_results exists in session state
    if hasattr(st.session_state, 'arxiv_results') and st.session_state.arxiv_results:
        st.subheader("Search Results")
        
        for i, paper in enumerate(st.session_state.arxiv_results):
            with st.expander(f"{i+1}. {paper['title']}"):
                st.write(f"**Authors:** {', '.join(paper['authors'][:3])}")
                if len(paper['authors']) > 3:
                    st.write(f"*... and {len(paper['authors']) - 3} more*")
                
                st.write(f"**Published:** {paper['published']}")
                st.write(f"**Categories:** {', '.join(paper['categories'])}")
                
                st.write("**Abstract:**")
                st.write(paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract'])
                
                st.write(f"[View PDF]({paper['pdf_url']})")
                
                # Download option
                if st.button(f"Download and Process", key=f"download_{i}"):
                    with st.spinner("Downloading and processing paper..."):
                        response = requests.post(
                            f"{BACKEND_URL}/arxiv-download", 
                            params={"arxiv_id": paper['arxiv_id']}
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"Paper downloaded successfully! {result['chunks_processed']} chunks processed.")
                            
                            # Refresh document list
                            load_documents()
                        else:
                            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

def render_management_section():
    st.header("📊 Document Management")
    
    if not st.session_state.processed_documents:
        st.info("No documents have been processed yet.")
        return
    
    st.subheader("Processed Documents")
    
    for doc in st.session_state.processed_documents:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{doc['filename']}**")
            st.write(f"Chunks: {doc['chunks']} | Pages: {doc.get('pages', 'N/A')}")
        
        with col2:
            if st.button(f"Query", key=f"query_btn_{doc['filename']}"):
                st.session_state.selected_doc_query = doc['filename']
                st.experimental_set_query_params(page="Query Documents")
                st.rerun()
        
        with col3:
            if st.button(f"Delete", key=f"delete_btn_{doc['filename']}"):
                with st.spinner("Deleting document..."):
                    response = requests.delete(
                        f"{BACKEND_URL}/delete-document", 
                        params={"filename": doc['filename']}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Document deleted: {result['filename']}")
                        # Refresh document list
                        load_documents()
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

if __name__ == "__main__":
    main()