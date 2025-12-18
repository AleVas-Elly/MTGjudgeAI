import time
import os
import sys
import keyring
from groq import Groq
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
from dotenv import load_dotenv

# Re-use constants from main.py
SERVICE_NAME = "mtg_rulebook_ai"
USERNAME = "groq_api_key"
INDEX_PATH = 'data/rulebook_index.pkl'
TOP_K_CHUNKS = 50

# Testing Questions
QUESTIONS = [
    "What happens if I cast a spell with cascade and I hit a spell with X in its cost?",
    "Can I use a fetch land to find a Triome?",
    "How does Layer 7 work with Humility and Giant Growth?",
    "If I have Teferi, Time Raveler, can my opponent cast spells with Flash during my turn?",
    "What is the interaction between Blood Moon and Urza's Saga?",
    "Does Deathtouch work with Trample?",
    "How many poison counters does a player need to lose the game?",
    "Can I counter a spell that says it can't be countered with a spell that exiles it?",
    "If I have a Doubling Season, how many loyalty counters does a Planeswalker enter with?",
    "What happens if I control two copies of the same Legendary creature?"
]

def get_api_key():
    api_key = keyring.get_password(SERVICE_NAME, USERNAME)
    if not api_key:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
    return api_key

def load_index():
    if not os.path.exists(INDEX_PATH):
        print(f"❌ Index not found at {INDEX_PATH}")
        sys.exit(1)
    with open(INDEX_PATH, 'rb') as f:
        return pickle.load(f)

def retrieve_relevant_chunks(query, index_data, model, top_k=TOP_K_CHUNKS):
    query_embedding = model.encode([query])[0]
    chunk_embeddings = index_data['embeddings']
    similarities = np.dot(chunk_embeddings, query_embedding) / (
        np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    return [index_data['chunks'][i] for i in top_indices]

def run_test():
    print("🚀 Starting Load Test for MTG Rulebook AI Judge")
    print(f"   Testing {len(QUESTIONS)} questions")
    
    api_key = get_api_key()
    if not api_key:
        print("❌ No API key found. Please run src/main.py first to set it up.")
        return

    client = Groq(api_key=api_key)
    index_data = load_index()
    embedding_model = SentenceTransformer(index_data['model_name'])
    
    results = []
    start_test_time = time.time()
    
    for i, question in enumerate(QUESTIONS): # Test all 10 questions
        print(f"[{i+1}/10] Processing: {question[:50]}...")
        
        start_time = time.time()
        try:
            # 1. Retrieval
            relevant_chunks = retrieve_relevant_chunks(question, index_data, embedding_model, top_k=TOP_K_CHUNKS)
            context = "\n\n".join([f"[Rule {c['rule_num']}]\n{c['text']}" for c in relevant_chunks])
            
            # 2. Generation
            system_instruction = f"You are an expert MTG Judge. Answer based on these rules:\n\n{context}"
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": question}
                ],
                temperature=0.3
            )
            
            end_time = time.time()
            duration = end_time - start_time
            results.append(duration)
            print(f"   ✅ Done in {duration:.2f}s")
            
            # Small delay just to be safe
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(None)
            time.sleep(2)
            
    end_test_time = time.time()
    total_duration = end_test_time - start_test_time
    
    # Analysis
    valid_results = [r for r in results if r is not None]
    if valid_results:
        avg_time = sum(valid_results) / len(valid_results)
        qpm = 60 / avg_time
        print("\n--- Load Test Results ---")
        print(f"Total Questions: {len(QUESTIONS)}")
        print(f"Successful: {len(valid_results)}")
        print(f"Total Time: {total_duration:.2f}s")
        print(f"Average Time per Question: {avg_time:.2f}s")
        print(f"Measured Throughput: {qpm:.2f} Questions Per Minute (QPM)")
        
        if qpm >= 10:
            print("🚀 Performance: EXCELLENT (meets 10 QPM goal)")
        elif qpm >= 5:
            print("📈 Performance: GOOD (meets 5 QPM goal)")
        else:
            print("⚠️  Performance: SLOW (below 5 QPM goal)")
    else:
        print("❌ No successful queries to analyze.")

if __name__ == "__main__":
    run_test()
