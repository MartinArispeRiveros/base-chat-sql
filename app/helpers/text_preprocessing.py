import re
import spacy
import unicodedata
import pdfplumber

def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

def split_text_into_chunks(text, chunk_size=500):
    sentences = re.split(r'(?<=\.)\s+', text)
    chunks = []
    chunk = ""
    for sentence in sentences:
        if len(chunk + sentence) > chunk_size:
            chunks.append(chunk)
            chunk = sentence
        else:
            chunk += " " + sentence
    if chunk:
        chunks.append(chunk)
    return chunks

def clean_text(text):
    text = re.sub(r'\x00', '', text)
    text = re.sub(r'\n+', ' ', text) 
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-zA-Z0-9\s.,;:¿?¡!]", "", text) 
    text = re.sub(r"\s+", " ", text).strip()

    return text.lower()

def lemmatize_text(text: str) -> str:
    nlp = spacy.load("es_core_news_sm")
    doc = nlp(text)
    lemmatized = " ".join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])
    return lemmatized

def normalize_text(text: str) -> str:
    text = re.sub(r'\x00', '', text)  
    text = re.sub(r'\n+', ' ', text)  
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-zA-Z0-9\s.,;:¿?¡!]", "", text)  
    text = re.sub(r"\s+", " ", text).strip()  
    
    return text.lower()