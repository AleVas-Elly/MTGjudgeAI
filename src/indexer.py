import re
import pickle
from sentence_transformers import SentenceTransformer
import numpy as np

RULEBOOK_PATH = 'data/MagicCompRules.txt'
INDEX_PATH = 'data/rulebook_index.pkl'

def parse_rulebook_into_chunks(rulebook_text):
    """Parse the rulebook into logical chunks by rule sections."""
    chunks = []
    
    # Split by major sections (numbered rules like "100.", "101.", etc.)
    # Each chunk will be a rule section with its subrules
    lines = rulebook_text.split('\n')
    current_chunk = []
    current_rule_num = None
    
    for line in lines:
        # Match rule numbers like "100.1", "702.19a", etc.
        rule_match = re.match(r'^(\d+\.\d+[a-z]?\.?)\s', line)
        
        if rule_match:
            # If we have a current chunk and we're starting a new major rule section
            rule_num = rule_match.group(1)
            major_rule = rule_num.split('.')[0]
            
            # Start new chunk when major rule changes or chunk gets too big
            if current_chunk and (
                current_rule_num is None or 
                current_rule_num.split('.')[0] != major_rule or
                len('\n'.join(current_chunk)) > 1500
            ):
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    chunks.append({
                        'text': chunk_text,
                        'rule_num': current_rule_num
                    })
                current_chunk = []
            
            current_rule_num = rule_num
        
        if line.strip():
            current_chunk.append(line)
    
    # Add final chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk).strip()
        if chunk_text:
            chunks.append({
                'text': chunk_text,
                'rule_num': current_rule_num or 'unknown'
            })
    
    return chunks

def create_index():
    """Create semantic index of the rulebook."""
    print("📚 Loading rulebook...")
    with open(RULEBOOK_PATH, 'r', encoding='utf-8') as f:
        rulebook_text = f.read()
    
    print("✂️  Parsing rulebook into chunks...")
    chunks = parse_rulebook_into_chunks(rulebook_text)
    print(f"   Created {len(chunks)} chunks")
    
    print("🧠 Loading embedding model (this may take a moment)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("🔢 Generating embeddings...")
    chunk_texts = [chunk['text'] for chunk in chunks]
    embeddings = model.encode(chunk_texts, show_progress_bar=True)
    
    print("💾 Saving index...")
    index_data = {
        'chunks': chunks,
        'embeddings': embeddings,
        'model_name': 'all-MiniLM-L6-v2'
    }
    
    with open(INDEX_PATH, 'wb') as f:
        pickle.dump(index_data, f)
    
    print(f"✅ Index created successfully!")
    print(f"   Chunks: {len(chunks)}")
    print(f"   Embedding dimensions: {embeddings.shape}")
    print(f"   Saved to: {INDEX_PATH}")

if __name__ == "__main__":
    create_index()
