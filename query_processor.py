import groq
import re
from typing import List, Dict
from config import Config

class QueryProcessor:
    def __init__(self):
        self.client = groq.Client(api_key=Config.GROQ_API_KEY)
    
    def detect_arxiv_request(self, query: str) -> bool:
        """Detect if the user is asking to find research papers"""
        arxiv_keywords = [
            "find paper", "search for paper", "arxiv", "research paper",
            "academic paper", "scientific paper", "look up paper",
            "find research", "search for research", "scholarly article"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in arxiv_keywords)
    
    def process_query(self, query: str, context: List[Dict]) -> str:
        """Process user query with enhanced detail and length"""
        if not context:
            return "I couldn't find any relevant information in the uploaded documents to answer your question."
        
        # Detect technical/mathematical queries for special handling
        if self._is_technical_query(query):
            return self._process_technical_query(query, context)
        elif self._is_complex_query(query):
            return self._process_complex_query(query, context)
        else:
            return self._process_standard_query(query, context)
    
    def _process_standard_query(self, query: str, context: List[Dict]) -> str:
        """Process standard queries with enhanced detail"""
        context_text = self._format_context(context)
        
        prompt = f"""Based strictly on the following document context, provide a comprehensive, detailed answer to the user's question.

CONTEXT:
{context_text}

QUESTION: {query}

IMPORTANT INSTRUCTIONS:
1. Provide a thorough, detailed explanation using all relevant information from the context
2. Structure your answer with clear paragraphs and logical flow
3. Include specific examples, details, and nuances mentioned in the context
4. Do NOT use any special tokens, XML tags, or formatting markers
5. If certain information is not in the context, acknowledge this while providing what is available
6. Aim for a comprehensive response that fully addresses the question

ANSWER:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Slightly higher temperature for more varied responses
                max_tokens=1500  # Increased token limit for detailed responses
            )
            
            raw_response = response.choices[0].message.content
            cleaned_response = self._format_response(raw_response)
            
            # Check if response is too brief and needs expansion
            if self._is_response_too_brief(cleaned_response, query):
                return self._expand_brief_response(query, context, cleaned_response)
                
            return cleaned_response
            
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def _process_technical_query(self, query: str, context: List[Dict]) -> str:
        """Specialized processing for technical/mathematical queries with enhanced detail"""
        context_text = self._format_context(context)
        
        prompt = f"""You are a technical research assistant. Based strictly on the following document context, provide a comprehensive, detailed answer to the user's technical question.

CONTEXT:
{context_text}

TECHNICAL QUESTION: {query}

IMPORTANT INSTRUCTIONS:
1. Provide an exhaustive, detailed explanation using all relevant technical information from the context
2. Include mathematical formulations, theorems, proofs, or algorithms when available
3. Explain the significance, implications, and applications of the concepts
4. Compare and contrast with related concepts mentioned in the context
5. Structure your answer with clear sections and logical flow
6. Do NOT use any special tokens, XML tags, or formatting markers
7. If information is incomplete, acknowledge this while providing what is available
8. Aim for a comprehensive technical explanation that would satisfy a researcher

DETAILED TECHNICAL ANSWER:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Lower temperature for more precise technical answers
                max_tokens=2000  # Even more tokens for technical explanations
            )
            
            raw_response = response.choices[0].message.content
            cleaned_response = self._format_response(raw_response)
            
            # Check if technical response needs expansion
            if self._is_response_too_brief(cleaned_response, query):
                return self._expand_technical_response(query, context, cleaned_response)
                
            return cleaned_response
            
        except Exception as e:
            return f"Error processing technical query: {str(e)}"
    
    def _process_complex_query(self, query: str, context: List[Dict]) -> str:
        """Handle complex queries that require multi-faceted answers"""
        context_text = self._format_context(context)
        
        prompt = f"""Based strictly on the following document context, provide a comprehensive, multi-faceted answer to the user's complex question.

CONTEXT:
{context_text}

COMPLEX QUESTION: {query}

IMPORTANT INSTRUCTIONS:
1. Provide a thorough, multi-part answer that addresses all aspects of the question
2. Structure your answer with clear sections for different facets of the question
3. Include examples, evidence, and detailed explanations from the context
4. Discuss implications, limitations, and applications when relevant
5. Do NOT use any special tokens, XML tags, or formatting markers
6. If the context doesn't cover all aspects, acknowledge this while providing what is available
7. Aim for a comprehensive response that fully explores the question

COMPREHENSIVE ANSWER:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.25,
                max_tokens=1800
            )
            
            return self._format_response(response.choices[0].message.content)
            
        except Exception as e:
            return f"Error processing complex query: {str(e)}"
    
    def _is_technical_query(self, query: str) -> bool:
        """Detect technical or mathematical queries"""
        technical_indicators = [
            'divergence', 'convex', 'differentiable', 'generator',
            'mathematical', 'theorem', 'proof', 'lemma', 'corollary',
            'framework', 'methodology', 'algorithm', 'formal', 'definition',
            'bregman', 'loss', 'noise', 'vector', 'distribution', 'symmetric',
            'symmetrization', 'lemma', 'empirical', 'process', 'analysis',
            'model', 'statistical', 'probability', 'optimization'
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in technical_indicators)
    
    def _is_complex_query(self, query: str) -> bool:
        """Detect complex queries that need multi-faceted answers"""
        complex_indicators = [
            'compare', 'contrast', 'analyze', 'discuss', 'evaluate',
            'explain', 'describe', 'what are', 'how does', 'why does',
            'advantages', 'disadvantages', 'benefits', 'limitations',
            'impact', 'effect', 'relationship', 'difference', 'similar'
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in complex_indicators)
    
    def _is_response_too_brief(self, response: str, query: str) -> bool:
        """Determine if a response is too brief for the query"""
        # Count words in response and query
        response_word_count = len(response.split())
        query_word_count = len(query.split())
        
        # If response is less than 3x query length or under 100 words, it's likely too brief
        is_brief = (response_word_count < max(100, query_word_count * 3))
        
        # Also check if the response seems incomplete
        seems_incomplete = (
            response.endswith(('...', 'etc.', 'etc')) or
            len(response.split('. ')) < 3  # Fewer than 3 sentences
        )
        
        return is_brief or seems_incomplete
    
    def _expand_brief_response(self, query: str, context: List[Dict], brief_response: str) -> str:
        """Expand a brief response with more detail"""
        context_text = self._format_context(context)
        
        prompt = f"""The following is a brief response to a question. Please expand it into a more comprehensive, detailed answer using the provided context.

CONTEXT:
{context_text}

ORIGINAL QUESTION: {query}

BRIEF RESPONSE: {brief_response}

INSTRUCTIONS FOR EXPANSION:
1. Significantly expand the response with more detail, examples, and explanations
2. Use all relevant information from the context
3. Maintain accuracy but add depth and breadth to the answer
4. Structure the expanded response with clear paragraphs
5. Do NOT use any special tokens or formatting markers
6. Ensure the expanded response is comprehensive and thorough

EXPANDED DETAILED RESPONSE:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1200
            )
            
            return self._format_response(response.choices[0].message.content)
            
        except Exception as e:
            # If expansion fails, return the original response with a note
            return f"{brief_response}\n\n[Note: This response may be brief due to limitations in the available context]"
    
    def _expand_technical_response(self, query: str, context: List[Dict], brief_response: str) -> str:
        """Expand a brief technical response with more detail"""
        context_text = self._format_context(context)
        
        prompt = f"""The following is a brief technical response. Please expand it into a comprehensive technical explanation using the provided context.

CONTEXT:
{context_text}

TECHNICAL QUESTION: {query}

BRIEF TECHNICAL RESPONSE: {brief_response}

INSTRUCTIONS FOR EXPANSION:
1. Significantly expand the technical explanation with more depth and detail
2. Include mathematical formulations, proofs, or algorithms when available
3. Discuss implications, applications, and limitations
4. Compare with related concepts mentioned in the context
5. Structure the expanded response with clear technical sections
6. Do NOT use any special tokens or formatting markers
7. Ensure the expanded response is comprehensive for a technical audience

EXPANDED TECHNICAL RESPONSE:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.25,
                max_tokens=1500
            )
            
            return self._format_response(response.choices[0].message.content)
            
        except Exception as e:
            return f"{brief_response}\n\n[Note: This technical response may be brief due to limitations in the available context]"
    
    def _format_context(self, context: List[Dict]) -> str:
        """Format context with emphasis on technical content"""
        context_texts = []
        for doc in context:
            content = doc["content"]
            
            # Highlight mathematical content
            content = self._highlight_mathematical_content(content)
            
            context_texts.append(
                f"Source: {doc['metadata']['source']}, Page: {doc['metadata']['page']}\n"
                f"Content: {content}"
            )
        
        return "\n\n".join(context_texts)
    
    def _highlight_mathematical_content(self, content: str) -> str:
        """Highlight mathematical expressions and definitions"""
        # Add emphasis to mathematical notation
        content = re.sub(r'(\$[^$]+\$)', r'**\1**', content)  # LaTeX math
        content = re.sub(r'([A-Z][a-z]*\s+[A-Z][a-z]+\s+[A-Z][a-z]+)', r'**\1**', content)  # Technical terms
        content = re.sub(r'(Definition|Theorem|Lemma|Corollary|Proof):', r'**\1:**', content)
        
        return content
    
    def _format_response(self, response: str) -> str:
        """Comprehensive response cleaning and formatting"""
        # Remove all special tokens and formatting artifacts
        response = self._remove_special_tokens(response)
        
        # Fix mathematical formatting
        response = self._clean_mathematical_content(response)
        
        # Ensure proper text structure
        response = self._ensure_proper_formatting(response)
        
        return response
    
    def _remove_special_tokens(self, response: str) -> str:
        """Remove all special tokens and formatting artifacts"""
        # Common special tokens to remove
        special_tokens = [
            r'<\|.*?\|>',  # <|header_start|>, <|endoftext|>, etc.
            r'\[.*?\]',    # [INST], [/INST], etc.
            r'\(.*?\)',    # (smile), (laugh), etc.
            r'\{\{.*?\}\}', # {{user}}, {{assistant}}, etc.
            r'\\[a-zA-Z]+\{.*?\}',  # \command{content}
        ]
        
        for pattern in special_tokens:
            response = re.sub(pattern, '', response)
        
        # Remove specific common artifacts
        artifacts = [
            'header_start', 'endoftext', 'endofsequence',
            'startoftext', 'pad', 'unk', 'sep', 'cls', 'mask'
        ]
        
        for artifact in artifacts:
            response = response.replace(f'<|{artifact}|>', '')
            response = response.replace(f'[{artifact}]', '')
            response = response.replace(f'({artifact})', '')
        
        return response.strip()
    
    def _clean_mathematical_content(self, response: str) -> str:
        """Clean and format mathematical content"""
        # Fix LaTeX formatting issues
        response = re.sub(r'\\\(', '$', response)
        response = re.sub(r'\\\)', '$', response)
        response = re.sub(r'\\\[', '$$', response)
        response = re.sub(r'\\\]', '$$', response)
        
        # Fix common mathematical notation issues
        math_replacements = {
            r'\\times': '×',
            r'\\cdot': '·',
            r'\\infty': '∞',
            r'\\sum': '∑',
            r'\\prod': '∏',
            r'\\int': '∫',
            r'\\partial': '∂',
            r'\\nabla': '∇',
            r'\\alpha': 'α',
            r'\\beta': 'β',
            r'\\gamma': 'γ',
            r'\\theta': 'θ',
            r'\\lambda': 'λ',
            r'\\mu': 'μ',
            r'\\sigma': 'σ',
            r'\\phi': 'φ',
            r'\\psi': 'ψ',
            r'\\omega': 'ω'
        }
        
        for pattern, replacement in math_replacements.items():
            response = re.sub(pattern, replacement, response)
        
        return response
    
    def _ensure_proper_formatting(self, response: str) -> str:
        """Ensure the response has proper formatting and structure"""
        # Remove duplicate words and phrases
        response = re.sub(r'\b(\w+)\s+\1\b', r'\1', response)
        
        # Fix punctuation and spacing
        response = re.sub(r'\s+([.,!?;:])', r'\1', response)
        response = re.sub(r'([.,!?;:])(\w)', r'\1 \2', response)
        response = re.sub(r'\s+', ' ', response)
        
        # Ensure proper capitalization
        sentences = re.split(r'([.!?])\s+', response)
        formatted_sentences = []
        
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sentence = sentences[i]
                if sentence and len(sentence) > 1:
                    # Capitalize first letter
                    sentence = sentence[0].upper() + sentence[1:]
                    formatted_sentences.append(sentence)
                
                # Add punctuation if needed
                if i + 1 < len(sentences):
                    formatted_sentences.append(sentences[i + 1] + ' ')
        
        response = ''.join(formatted_sentences).strip()
        
        # Remove any remaining special characters at start/end
        response = re.sub(r'^[^a-zA-Z0-9"]+', '', response)
        response = re.sub(r'[^a-zA-Z0-9".!?]+$', '', response)
        
        return response
    
    def summarize_document(self, context: List[Dict]) -> str:
        """Generate a comprehensive summary with proper formatting"""
        if not context:
            return "No content available for summarization."
        
        context_text = "\n\n".join([doc["content"] for doc in context])
        
        prompt = f"""Please provide a comprehensive, well-structured summary of the following document content.

{context_text}

SUMMARY GUIDELINES:
1. Start with an overview of the main topic and objectives
2. Describe the key methodologies or approaches used
3. Highlight the main findings or results
4. Discuss conclusions and implications
5. Use clear section headings and proper formatting
6. Include important mathematical formulations if present
7. Keep the summary detailed but organized
8. Do NOT use any special tokens, XML tags, or formatting markers
9. Aim for a thorough summary that captures the essence of the document

COMPREHENSIVE SUMMARY:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500  # Increased for more detailed summaries
            )
            
            return self._format_response(response.choices[0].message.content)
        except Exception as e:
            return f"Error generating summary: {str(e)}"
