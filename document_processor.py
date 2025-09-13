import fitz  # PyMuPDF
import re
from typing import List, Dict, Any
import os

class DocumentProcessor:
    def __init__(self):
        self.section_patterns = {
            'abstract': r'abstract|summary',
            'introduction': r'introduction',
            'methodology': r'method|approach|experiment',
            'results': r'result|finding',
            'conclusion': r'conclusion|discussion',
            'reference': r'reference|bibliography'
        }
    
    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract structured text from PDF document"""
        doc = fitz.open(file_path)
        chunks = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # Simple chunking by page with metadata
            chunks.append({
                "content": text,
                "page": page_num + 1,
                "source": os.path.basename(file_path)
            })
        
        doc.close()
        return chunks
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            if end > len(text):
                end = len(text)
            
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end == len(text):
                break
                
            start = end - overlap
        
        return chunks