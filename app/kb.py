import os
import openai
import math

from .config import BASE_DIR

# Directory containing knowledge base documents (plain text files)
KB_DIR = os.path.join(BASE_DIR, 'kb_docs')

def load_docs():
    """Load all text documents from the KB_DIR."""
    docs = []
    if not os.path.isdir(KB_DIR):
        return docs
    for fname in os.listdir(KB_DIR):
        path = os.path.join(KB_DIR, fname)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            docs.append({'id': fname, 'text': text})
    return docs

def get_embedding(text):
    """Compute embedding for the given text using OpenAI."""
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=[text]
    )
    return response['data'][0]['embedding']

class KnowledgeBase:
    """
    Simple in-memory KB with embed-and-search functionality.
    """
    def __init__(self):
        self.docs = load_docs()
        # Pre-compute embeddings
        for doc in self.docs:
            doc['embedding'] = get_embedding(doc['text'])

    def query(self, text, top_k=3):
        """Return top_k most relevant documents for the query."""
        if not self.docs:
            return []
        q_emb = get_embedding(text)
        def score(doc):
            a = doc['embedding']
            # cosine similarity
            dot = sum(x * y for x, y in zip(a, q_emb))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_q = math.sqrt(sum(x * x for x in q_emb))
            return dot / (norm_a * norm_q) if norm_a and norm_q else 0
        scored = sorted(self.docs, key=score, reverse=True)
        return scored[:top_k]

# Single shared KB instance
kb = KnowledgeBase()