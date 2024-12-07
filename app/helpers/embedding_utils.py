import pdfplumber
import json

from sentence_transformers import SentenceTransformer
from app.helpers.text_preprocessing import normalize_text, split_text_into_chunks

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def process_pdf(file_path: str, chunk_size: int) -> list:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or "" 

    text = normalize_text(text)
    print("Texto limpio:", text) 
    chunks = split_text_into_chunks(text, chunk_size=chunk_size)
    
    return chunks

def create_vector_index(texts, embedding_model):
    embeddings = embedding_model.encode(texts, convert_to_tensor=False).tolist()
    vector_store = [{"text": text, "embedding": embedding} for text, embedding in zip(texts, embeddings)]
    return vector_store

def save_vector_store(vector_store, file_path):
    with open(file_path, "w") as f:
        json.dump(vector_store, f)

def load_vector_store(file_path):
    with open(file_path, "r") as f:
        vector_store = json.load(f)
    return vector_store

def combine_vector_stores(existing_store, new_store):
    combined_store = existing_store + new_store
    return combined_store