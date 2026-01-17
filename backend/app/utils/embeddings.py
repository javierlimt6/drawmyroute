import pickle
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
import numpy as np

INDEX_PATH = Path(__file__).parent.parent / "data" / "vector_index.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"

# Global model cache to avoid reloading
_model = None

def _get_model():
    global _model
    if _model is None:
        print(f"📥 Loading Sentence Transformer: {MODEL_NAME}...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def build_vector_index(semantic_index: list[dict]):
    """
    Builds a Semantic Vector index and saves it to disk.
    """
    print("🧠 Building Semantic Vector Index...")
    model = _get_model()
    
    # Corpus: "name tags..."
    corpus = [f"{item['name']} {' '.join(item.get('tags', []))}" for item in semantic_index]
    
    if not corpus:
        print("⚠️ Semantic index empty.")
        return

    # Compute Embeddings
    embeddings = model.encode(corpus, convert_to_tensor=True)
    
    # Convert to numpy for storage
    embeddings_np = embeddings.cpu().numpy()
    
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(embeddings_np, f)
        
    print(f"✅ Vector Index saved to {INDEX_PATH}")

def search_vector_index(query: str, top_k: int = 15) -> list[int]:
    """
    Returns indices of top_k semantic matches.
    """
    if not INDEX_PATH.exists():
        return []
        
    try:
        model = _get_model()
        
        with open(INDEX_PATH, "rb") as f:
            corpus_embeddings = pickle.load(f)
            
        query_embedding = model.encode(query, convert_to_tensor=True)
        
        # Ensure on CPU to match corpus_embeddings (numpy)
        query_embedding = query_embedding.cpu()
        
        # Compute Cosine Similarity
        hits = util.cos_sim(query_embedding, corpus_embeddings)[0]
        
        # Get top k
        top_results = hits.topk(k=min(top_k, len(hits)))
        
        # Result is (values, indices)
        indices = top_results.indices.tolist()
        
        return indices
        
    except Exception as e:
        print(f"⚠️ Vector search failed: {e}")
        return []
