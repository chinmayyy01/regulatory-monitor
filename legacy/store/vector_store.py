import os
import re
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from app.fetchers.base import Circular

CHROMA_PATH = os.getenv('CHROMA_DB_PATH', './data/chroma_db')

class CircularStore:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
        # self.embeddings = OpenAIEmbeddings()
        self.db = Chroma(collection_name='circulars', embedding_function=self.embeddings, persist_directory=CHROMA_PATH)
    
    @staticmethod
    def clean_text(text: str) -> str:
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\(\d+\s*kb\)', '', text)
        text = text.strip()
        return text
    
    def is_new(self, circular: Circular) -> bool:
        existing = self.db.get(where={"id": circular.id})
        if existing:
            return False
        query = (self.clean_text(circular.title) + ' ') * 3 + self.clean_text(circular.full_text[:300])
        results = self.db.similarity_search_with_score(query, k=1)
        if not results:
            return True
        doc, score = results[0]
        return score > 0.18 
    
    def add(self, circular: Circular):
        doc = Document(
            page_content= self.clean_text(circular.title) + ' ' + self.clean_text(circular.full_text[:500]),
            metadata = {
                'id': circular.id,
                'source': circular.source,
                'url': circular.url,
                'date': circular.published_date.isoformat(),
            }
        )
        self.db.add_documents([doc], ids=[circular.id])
        
    def filter_new(self, circulars: list[Circular]) -> list[Circular]:
        new_ones = []
        for c in circulars:
            if self.is_new(c):
                new_ones.append(c)
                self.add(c) # stores it now so next run knows about it
        return new_ones