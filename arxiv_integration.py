import requests
import os
import re
from typing import List, Dict, Optional
from config import Config
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

class ArxivIntegration:
    def __init__(self):
        self.base_url = "https://export.arxiv.org/api/query"
    
    def search_papers(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for papers on Arxiv using direct API calls"""
        try:
            # URL encode the query
            encoded_query = quote_plus(query)
            
            # Build the API request URL
            url = f"{self.base_url}?search_query={encoded_query}&start=0&max_results={max_results}"
            
            # Make the request
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse the XML response
            root = ET.fromstring(response.content)
            
            # Define XML namespaces
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                paper_data = {
                    "title": entry.find('atom:title', ns).text.strip() if entry.find('atom:title', ns) is not None else "No title",
                    "authors": [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)],
                    "abstract": entry.find('atom:summary', ns).text.strip() if entry.find('atom:summary', ns) is not None else "No abstract",
                    "published": entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else "No date",
                    "pdf_url": None,
                    "arxiv_id": entry.find('atom:id', ns).text.split('/')[-1] if entry.find('atom:id', ns) is not None else "No ID",
                    "categories": [cat.get('term') for cat in entry.findall('atom:category', ns)]
                }
                
                # Find the PDF link
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        paper_data["pdf_url"] = link.get('href')
                        break
                
                papers.append(paper_data)
            
            return papers
        
        except Exception as e:
            print(f"Error searching Arxiv: {e}")
            print(f"Request URL: {url if 'url' in locals() else 'Not available'}")
            return []
    
    def download_paper(self, arxiv_id: str, filename: Optional[str] = None) -> Optional[str]:
        """Download a paper from Arxiv by ID"""
        try:
            # Construct the PDF URL
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            # Determine filename
            if not filename:
                filename = f"{arxiv_id}.pdf"
            
            download_path = os.path.join(Config.UPLOAD_DIR, filename)
            
            # Download the PDF
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            # Save the file
            with open(download_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded paper to: {download_path}")
            return download_path
        
        except Exception as e:
            print(f"Error downloading paper: {e}")
            return None
    
    def process_arxiv_query(self, user_query: str) -> Dict:
        """
        Process a user query that might require Arxiv search
        Returns both search results and a natural language response
        """
        # Extract search terms from the query
        search_terms = self._extract_search_terms(user_query)
        
        if not search_terms:
            return {
                "response": "I couldn't determine what kind of paper you're looking for. Could you be more specific?",
                "papers": []
            }
        
        # Search for papers
        papers = self.search_papers(search_terms)
        
        if not papers:
            return {
                "response": f"I couldn't find any papers matching: '{search_terms}'. Try different search terms.",
                "papers": []
            }
        
        # Generate a natural language response
        response = self._generate_search_response(papers, search_terms)
        
        return {
            "response": response,
            "papers": papers
        }
    
    def _extract_search_terms(self, query: str) -> str:
        """Extract relevant search terms from user query"""
        # Remove common question phrases
        phrases_to_remove = [
            "find me", "look for", "search for", "papers about", 
            "research on", "articles about", "can you find",
            "show me", "recommend", "suggest"
        ]
        
        query_lower = query.lower()
        for phrase in phrases_to_remove:
            query_lower = query_lower.replace(phrase, "")
        
        # Remove question words
        question_words = ["what", "where", "when", "why", "how", "which", "who", "should", "could"]
        words = query_lower.split()
        filtered_words = [word for word in words if word not in question_words]
        
        return " ".join(filtered_words).strip()
    
    def _generate_search_response(self, papers: List[Dict], search_terms: str) -> str:
        """Generate a natural language response about the found papers"""
        if not papers:
            return f"I couldn't find any papers matching '{search_terms}'."
        
        response = f"I found {len(papers)} papers related to '{search_terms}':\n\n"
        
        for i, paper in enumerate(papers[:3], 1):  # Show top 3
            response += f"{i}. **{paper['title']}**\n"
            response += f"   Authors: {', '.join(paper['authors'][:2])}"
            if len(paper['authors']) > 2:
                response += f" et al.\n"
            else:
                response += "\n"
            response += f"   Published: {paper['published'][:10]}\n\n"
        
        if len(papers) > 3:
            response += f"... and {len(papers) - 3} more papers.\n\n"
        
        response += "Would you like me to download any of these papers for analysis?"
        
        return response

# Example usage
if __name__ == "__main__":
    arxiv_client = ArxivIntegration()
    
    # Test search
    results = arxiv_client.search_papers("machine learning", max_results=3)
    for paper in results:
        print(f"Title: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'][:2])}")
        print(f"PDF: {paper['pdf_url']}")
        print("---")
    
    # Test query processing
    response = arxiv_client.process_arxiv_query("Find me papers about quantum computing")
    print(f"\nResponse: {response['response']}")