import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.app.core.config import INDEX_PATH, TOP_K_CHUNKS

class RAGService:
    def __init__(self):
        self.index_data = self._load_index()
        self.model = SentenceTransformer(self.index_data['model_name'])

    def _load_index(self):
        """Loads the rulebook index from disk."""
        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError("Index not found. Run indexer first.")
        with open(INDEX_PATH, 'rb') as f:
            return pickle.load(f)

    def retrieve(self, query, history=None, top_k=TOP_K_CHUNKS):
        """Finds the most relevant rule chunks."""
        search_query = query
        if history and len(query.split()) < 5:
            last_user_q = history[-2] if len(history) >= 2 else ""
            search_query = f"{last_user_q} {query}"

        query_embedding = self.model.encode([search_query])[0]
        chunk_embeddings = self.index_data['embeddings']
        
        # Calculate cosine similarity
        similarities = np.dot(chunk_embeddings, query_embedding) / (
            np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [self.index_data['chunks'][i] for i in top_indices]
