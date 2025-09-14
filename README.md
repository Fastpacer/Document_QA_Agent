# Document Q&A AI Agent

A powerful AI-powered document querying system that allows you to upload PDF documents, ask questions about them, and search for relevant research papers from Arxiv.

🚨 Important Constraints & Limitations
This version has several important constraints due to its development stage and resource limitations:

1. Local Development Only
This application is designed for localhost environments only and is not configured for production deployment. It requires local file system access and runs on localhost.

2. Groq API Free Tier Limitations
The application uses Groq's free tier API, which has significant constraints:

Token Limits: Free tier has strict token limits (∼8000 tokens per minute)

Large Document Handling: Research papers and large documents may exceed token limits

Rate Limiting: API calls are rate-limited, which may cause timeouts with large files

Model Restrictions: Limited to specific models available on the free tier

3. Hardware Requirements
Requires sufficient RAM for embedding models and document processing

PDF processing can be memory-intensive for large documents

Vector database storage requires local disk space

4. Document Size Limitations
Very large research papers (>50 pages) may not process completely

Complex mathematical content may not be fully captured

Token limits may truncate responses for complex queries

✨ Features (Within Constraints)
Document Upload & Processing: Upload and process PDF documents (within size limits)

Basic Querying: Ask questions about uploaded documents (simpler queries work best)

Document Summarization: Generate summaries of specific documents

Research Paper Search: Find relevant academic papers from Arxiv (basic searches)

Document Management: View and manage processed documents

🛠️ Installation & Setup
Prerequisites
Python 3.8+

Groq API account (free tier)

Minimum 8GB RAM recommended

2GB+ free disk space for document storage

1. Clone the Repository
bash
git clone https://github.com/yourusername/document-qa-agent.git
cd document-qa-agent
2. Create Virtual Environment
bash
python -m venv env
# On Windows:
env\Scripts\activate
# On Mac/Linux:
source env/bin/activate
3. Install Dependencies
bash
pip install -r requirements.txt
4. Set Up Environment Variables
bash
# Copy the example environment file
cp .env.example .env
# Edit .env and add your Groq API key
echo "GROQ_API_KEY=your_actual_groq_api_key_here" > .env
5. Get Your Groq API Key
Sign up at https://console.groq.com/

Create a new API key (free tier)

Add it to your .env file

🚀 Usage
Starting the Backend Server
bash
python app.py
The API server will start at http://localhost:8000

Starting the Streamlit Frontend (in a new terminal)
bash
streamlit run streamlit_app.py
The web interface will open at http://localhost:8501

Recommended Usage Pattern
Start with smaller documents (under 30 pages)

Use simple, focused queries rather than complex multi-part questions

Process documents one at a time to avoid overwhelming the API

Monitor console output for token limit warnings

📊 Performance Expectations
What Works Well
Small to medium-sized documents (5-25 pages)

Direct factual questions

Simple summary requests

Basic research paper searches

Known Limitations
Large research papers: May hit token limits or time out

Complex mathematical queries: May not capture all nuances

Multi-part questions: May receive incomplete responses

High-volume processing: Free tier rate limits will be exceeded

🏗️ Architecture
text
Frontend (Streamlit) → Backend (FastAPI) → Vector Database (ChromaDB)
                             |
                             → Groq LLM API (Free Tier)
                             → Arxiv API
🔮 Future Enhancements (When Constraints Are Removed)
Cloud deployment with scalable infrastructure

Paid API tier for higher limits and better performance

Advanced document processing with better large-file support

User authentication and authorization

Support for more document types

Real-time collaboration features

🤝 Contributing
This is currently a personal project with significant constraints. Contributions that address the current limitations are welcome, but please be aware of the free-tier API constraints.

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

⚠️ Troubleshooting Common Issues
Token Limit Errors
bash
# Error: Request too large for model
Solution: Use smaller documents or break queries into smaller parts
Rate Limit Errors
bash
# Error: Rate limit exceeded
Solution: Wait before making additional requests or process fewer documents
Large Document Failures
bash
# Error: Document processing failed
Solution: Use smaller documents or split large documents into sections
Memory Issues
bash
# Error: Out of memory
Solution: Close other applications or use a machine with more RAM
🆘 Support
For issues related to this version, please check:

Groq API key is properly set in .env

Backend server is running on port 8000

You're not exceeding free tier limits

Documents are within recommended size limits

📄 Document Recommendations
For best results, use:

Research papers under 30 pages

Documents with clear text (not scanned images)

PDFs with proper text layers (not image-only PDFs)

Well-structured documents with sections and headings
