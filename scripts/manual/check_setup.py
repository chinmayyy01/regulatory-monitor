import os 
from dotenv import load_dotenv 
load_dotenv()  # Reads your .env file into environment variables 
groq_key = os.getenv('GROQ_API_KEY') 
if groq_key and groq_key.startswith('gsk_'): 
    print('✓ Groq API key loaded correctly') 
else: 
    print('✗ Groq key missing — check your .env file') 
try: 
    from sentence_transformers import SentenceTransformer 
    print('✓ sentence-transformers installed') 
except ImportError: 
    print('✗ sentence-transformers missing — run pip install -r requirements.txt') 
try: 
    from langchain_groq import ChatGroq 
    print('✓ langchain-groq installed') 
except ImportError: 
    print('✗ langchain-groq missing') 