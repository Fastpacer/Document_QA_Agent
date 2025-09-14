# Document Q&A AI Agent
A powerful AI-powered document querying system for PDF analysis and research paper discovery.


⚠️ Important Constraints
This is a localhost-only MVP with significant limitations:

Local Development Only: Not configured for production deployment

Free Tier Limits: Uses Groq's free API with strict token limits (~8000 TPM)

Large File Issues: Research papers >30 pages may fail processing

Hardware Demands: Requires 8GB+ RAM and 2GB+ storage

✨ Features
📄 PDF document processing and text extraction

❓ AI-powered question answering

📝 Document summarization

🔍 Arxiv research paper search

🗂️ Document management interface

🚀 Quick Start
Installation
bash
git clone https://github.com/yourusername/document-qa-agent.git
cd document-qa-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
Configuration
Get free API key from console.groq.com

Create .env file:

env
GROQ_API_KEY=your_actual_api_key_here
Running
bash
# Terminal 1 - Backend API
python app.py

# Terminal 2 - Frontend
streamlit run streamlit_app.py
Access at:

API Docs: http://localhost:8000/docs

Web UI: http://localhost:8501

📖 Usage
Upload PDFs through the web interface

Ask questions about your documents

Get summaries of specific files

Search Arxiv for related research papers

Recommended Usage
Stick to documents under 30 pages

Use specific, focused queries

Process files one at a time

Monitor console for token limit warnings

🐛 Troubleshooting
Common Issues
Rate Limits: Wait between requests or use smaller documents

Memory Issues: Close other applications or add more RAM

Processing Failures: Try smaller files or split large documents

🔮 Future Enhancements
Cloud deployment capabilities

Paid API tier integration

Advanced document processing

User authentication system

Enhanced large file support


Note: This MVP works best with smaller documents and simple queries due to free-tier API constraints. Performance with complex research papers will be limited until upgraded.
