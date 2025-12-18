import re
import pickle
import os
from sentence_transformers import SentenceTransformer
import numpy as np
from src.config import RULEBOOK_PATH, INDEX_PATH
from src.utils.io import ensure_data_dir

def parse_rulebook_into_chunks(rulebook_text):
    """Parses the rulebook into logically coherent chunks."""
    chunks = []
    lines = rulebook_text.split('\n')
    current_chunk = []
    current_rule_num = None
    
    for line in lines:
        rule_match = re.match(r'^(\d+\.\d+[a-z]?\.?)\s', line)
        if rule_match:
            rule_num = rule_match.group(1)
            major_rule = rule_num.split('.')[0]
            
            if current_chunk and (
                current_rule_num is None or 
                current_rule_num.split('.')[0] != major_rule or
                len('\n'.join(current_chunk)) > 1500
            ):
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    chunks.append({'text': chunk_text, 'rule_num': current_rule_num})
                current_chunk = []
            
            current_rule_num = rule_num
        
        if line.strip():
            current_chunk.append(line)
    
    if current_chunk:
        chunk_text = '\n'.join(current_chunk).strip()
        if chunk_text:
            chunks.append({'text': chunk_text, 'rule_num': current_rule_num or 'unknown'})
    
    return chunks

def create_index():
    """Generates the semantic index for the RAG service."""
    ensure_data_dir()
    
    if not os.path.exists(RULEBOOK_PATH):
        print(f"Error: Rulebook not found at {RULEBOOK_PATH}")
        return

    print("Loading rulebook documents...")
    with open(RULEBOOK_PATH, 'r', encoding='utf-8') as f:
        rulebook_text = f.read()
    
    chunks = parse_rulebook_into_chunks(rulebook_text)
    print(f"Initialised {len(chunks)} rule segments.")
    
    print("Loading transformer model...")
    model_name = 'all-MiniLM-L6-v2'
    model = SentenceTransformer(model_name)
    
    print("Generating vector embeddings...")
    texts = [c['text'] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    index_data = {
        'chunks': chunks,
        'embeddings': embeddings,
        'model_name': model_name
    }
    
    with open(INDEX_PATH, 'wb') as f:
        pickle.dump(index_data, f)
    
    print(f"Index successfully saved to {INDEX_PATH}")

if __name__ == "__main__":
    create_index()
