import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    UPLOAD_DIR = "C:\\Users\\Hp\\Desktop\\Document_QA_Agent\\data\\documents"
    VECTOR_DB_DIR = "C:\\Users\\Hp\\Desktop\\Document_QA_Agent\\data\\vector_db"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    EMBEDDING_MODEL = "mpnet"
    # Technical content handling
    TECHNICAL_CHUNK_SIZE = 1200  # Larger chunks for technical content
    MAX_TECHNICAL_TOKENS = 1200  # More tokens for technical responses
    ENABLE_MATH_HIGHLIGHTING = True

    @staticmethod
    def ensure_directories_exist():
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        os.makedirs(Config.VECTOR_DB_DIR, exist_ok=True)
