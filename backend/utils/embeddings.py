from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from config import get_settings

settings = get_settings()
model = SentenceTransformer('all-MiniLM-L6-v2')

def split_transcript_into_chunks(transcript: str, chunk_size: int = 300) -> List[str]:
    """Split transcript into chunks of roughly equal size at sentence boundaries."""
    sentences = transcript.split('. ')
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence.split())
        if current_length + sentence_length > chunk_size:
            chunks.append('. '.join(current_chunk) + '.')
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length
    
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks

def get_embeddings(text: str) -> np.ndarray:
    """Generate embeddings for a piece of text."""
    with torch.no_grad():
        return model.encode(text)

def find_relevant_chunks(query: str, chunks: List[str], embeddings: List[np.ndarray], top_k: int = 3) -> List[str]:
    """Find the most relevant chunks for a given query."""
    query_embedding = get_embeddings(query)
    
    # Calculate similarities
    similarities = [np.dot(query_embedding, chunk_embedding) / 
                   (np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)) 
                   for chunk_embedding in embeddings]
    
    # Get indices of top_k most similar chunks
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    return [chunks[i] for i in top_indices] 