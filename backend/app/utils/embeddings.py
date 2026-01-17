import pickle
import os
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

INDEX_PATH = Path(__file__).parent.parent / "data" / "vector_index.pkl"

def build_vector_index(semantic_index: list[dict]):
    """
    Builds a TF-IDF index from the semantic index and saves it to disk.
    """
    print("🧠 Building Vector Index...")
    
    # Corpus: "name tag1 tag2 tag3..."
    # We repeat the name to give it more weight
    corpus = [f"{item['name']} {item['name']} {' '.join(item.get('tags', []))}" for item in semantic_index]
    
    if not corpus:
        print("⚠️ Semantic index empty, skipping vector build.")
        return

    vectorizer = TfidfVectorizer(stop_words='english')
    matrix = vectorizer.fit_transform(corpus)
    
    # Save both vectorizer and matrix
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump((vectorizer, matrix), f)
        
    print(f"✅ Vector Index saved to {INDEX_PATH}")

def search_vector_index(query: str, top_k: int = 15) -> list[int]:
    """
    Returns indices of top_k matches.
    """
    if not INDEX_PATH.exists():
        return []
        
    try:
        with open(INDEX_PATH, "rb") as f:
            vectorizer, matrix = pickle.load(f)
            
        query_vec = vectorizer.transform([query])
        
        # Calculate cosine similarity (dot product for normalized vectors)
        similarities = (matrix * query_vec.T).toarray().flatten()
        
        # Get top K
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # Filter out zero similarity
        results = [i for i in top_indices if similarities[i] > 0]
        return results
        
    except Exception as e:
        print(f"⚠️ Vector search failed: {e}")
        return []
