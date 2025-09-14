import fitz  # PyMuPDF
import re
import os
from typing import List, Dict

class DocumentProcessor:
    def __init__(self):
        self.mathematical_patterns = [
            r'\\[(\w+)|[^]]+]',  # LaTeX commands
            r'\$[^$]+\$',        # Inline math
            r'\$\$[^$]+\$\$',    # Display math
            r'\\begin\{[^}]+\}', # LaTeX environments
        ]
    
    def extract_text_from_pdf(self, file_path: str) -> List[Dict]:
        """Extract text from PDF with mathematical content preservation"""
        doc = fitz.open(file_path)
        chunks = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # Enhanced text extraction for technical documents
            page_chunks = self._process_technical_text(text, page_num, os.path.basename(file_path))
            chunks.extend(page_chunks)
        
        doc.close()
        return chunks
    
    def _process_technical_text(self, text: str, page_num: int, source: str) -> List[Dict]:
        """Process text with special handling for technical content"""
        # Preserve mathematical notation and technical structure
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line contains important technical content
            is_technical = self._is_technical_content(line)
            
            if is_technical and current_chunk:
                # Save current chunk and start a new one for technical content
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, page_num, source))
                current_chunk = [line]
                current_length = len(line)
            elif current_length + len(line) > 1200:  # Slightly larger chunks for technical content
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, page_num, source))
                current_chunk = [line]
                current_length = len(line)
            else:
                current_chunk.append(line)
                current_length += len(line)
        
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, page_num, source))
        
        return chunks
    
    def _is_technical_content(self, text: str) -> bool:
        """Check if text contains technical or mathematical content"""
        technical_indicators = [
            'definition', 'theorem', 'lemma', 'corollary', 'proof',
            'proposition', 'equation', 'formula', 'matrix', 'vector',
            'function', 'derivative', 'integral', 'algorithm', 'complexity'
        ]
        
        # Check for mathematical notation
        has_math = any(re.search(pattern, text) for pattern in self.mathematical_patterns)
        
        # Check for technical terms
        text_lower = text.lower()
        has_technical_terms = any(term in text_lower for term in technical_indicators)
        
        return has_math or has_technical_terms
    
    def _create_chunk(self, lines: List[str], page_num: int, source: str) -> Dict:
        """Create a chunk with metadata"""
        content = '\n'.join(lines)
        
        # Add technical content flag
        is_technical = self._is_technical_content(content)
        
        return {
            "content": content,
            "page": page_num + 1,
            "source": source,
            "is_technical": is_technical
        }
