import groq
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
            "find research", "search for research", "scholarly article",
            "find me papers", "search for articles", "look for studies"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in arxiv_keywords)
    
    def process_query(self, query: str, context: List[Dict]) -> str:
        """Process user query with context using Groq API"""
        if not context:
            return "I couldn't find any relevant information in the uploaded documents to answer your question."
        
        context_text = "\n\n".join([
            f"Source: {doc['metadata']['source']}, Page: {doc['metadata']['page']}\n"
            f"Content: {doc['content'][:500]}..."  # Limit context length
            for doc in context
        ])
        
        prompt = f"""Based on the following document context, answer the user's question.

Context:
{context_text}

User Question: {query}

Please provide a concise and accurate answer based only on the provided context.
If the answer cannot be found in the context, say "I cannot find this information in the provided documents."
"""
        
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",  # Using a free model from Groq
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def summarize_document(self, context: List[Dict]) -> str:
        """Generate a summary of the document"""
        context_text = "\n\n".join([doc["content"] for doc in context])
        
        prompt = f"""Please provide a comprehensive summary of the following document content:

{context_text}

Summary:"""
        
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"