import os
import sys
import keyring
import pickle
from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer
import numpy as np

# Load environment variables (optional, for other configs)
load_dotenv()

RULEBOOK_PATH = 'data/MagicCompRules.txt'
INDEX_PATH = 'data/rulebook_index.pkl'
SERVICE_NAME = "mtg_rulebook_ai"
USERNAME = "gemini_api_key"
TOP_K_CHUNKS = 50  # Retrieve top 50 most relevant chunks (~40-50k tokens)

def ensure_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs('data', exist_ok=True)
    print("✅ Directory structure verified")

def get_api_key():
    """Retrieves the API key from the system keyring or prompts the user."""
    # Try getting from keychain first
    api_key = keyring.get_password(SERVICE_NAME, USERNAME)
    
    # If not in keychain, check env var as backup
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("\n⚠️  Gemini API Key not found in Keychain or environment.")
        print("You can get a free key from: https://aistudio.google.com/app/apikey")
        print("Required for the first run only. It will be saved securely to your System Keychain.")
        api_key = input("Please paste your API Key here: ").strip()
        if not api_key:
            print("Error: API Key is required to proceed.")
            sys.exit(1)
        
        # Save to keychain
        try:
            keyring.set_password(SERVICE_NAME, USERNAME, api_key)
            print("✅ Key saved securely to System Keychain!")
        except Exception as e:
            print(f"⚠️  Could not save to keychain: {e}")
            print("You may need to enter it again next time.")

    return api_key

def load_index():
    """Load the pre-computed rulebook index."""
    if not os.path.exists(INDEX_PATH):
        print(f"\n❌ Index not found at {INDEX_PATH}")
        print("Please run 'python src/indexer.py' first to create the index.")
        sys.exit(1)
    
    print("📚 Loading rulebook index...")
    with open(INDEX_PATH, 'rb') as f:
        index_data = pickle.load(f)
    
    print(f"   Loaded {len(index_data['chunks'])} rule chunks")
    return index_data

def retrieve_relevant_chunks(query, index_data, model, top_k=TOP_K_CHUNKS):
    """Retrieve the most relevant rule chunks for a query."""
    # Generate query embedding
    query_embedding = model.encode([query])[0]
    
    # Calculate cosine similarity with all chunks
    chunk_embeddings = index_data['embeddings']
    similarities = np.dot(chunk_embeddings, query_embedding) / (
        np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top-k most similar chunks
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    relevant_chunks = [index_data['chunks'][i] for i in top_indices]
    return relevant_chunks

def main():
    print("🔮 MTG Rulebook AI Judge (RAG Edition) 🔮")
    print("------------------------------------------")
    
    # Ensure directory structure exists
    ensure_directories()
    
    # Setup
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    
    # Load index
    index_data = load_index()
    
    # Load embedding model
    print("🧠 Loading embedding model...")
    embedding_model = SentenceTransformer(index_data['model_name'])
    
    print(f"\n✅ Ready! Using RAG with top-{TOP_K_CHUNKS} relevant chunks per query")
    print("   This allows 5-10 questions per minute with high accuracy!")
    print("\nAsk any question about Magic rules. (Type 'quit' to exit)")
    print("---------------------------------------------------------------")

    # Chat history
    history = []

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue

            print("🔍 Finding relevant rules...", end="\r")
            
            # Retrieve relevant chunks
            relevant_chunks = retrieve_relevant_chunks(
                user_input, 
                index_data, 
                embedding_model,
                top_k=TOP_K_CHUNKS
            )
            
            # Build context from relevant chunks
            context = "\n\n".join([
                f"[Rule {chunk['rule_num']}]\n{chunk['text']}" 
                for chunk in relevant_chunks
            ])
            
            # System instruction with retrieved context
            system_instruction = f"""You are an expert Magic: The Gathering Level 3 Judge with exceptional teaching skills. Your mission is to provide clear, concise, and practical answers to rules questions.

CRITICAL: Pay extremely close attention to timing restrictions, activation costs, and conditions in the rules. Many abilities have restrictions like "Activate only as a sorcery" or "Activate only during combat" - these MUST be respected in your examples.

RESPONSE STRUCTURE:
1. **Direct Answer** (1-2 sentences): Answer the question immediately and clearly.
2. **Key Rules** (bullet points): List only the most relevant rule citations with brief explanations. ALWAYS include timing restrictions if relevant.
3. **Game Example** (required): End EVERY response with a concrete, realistic game scenario that illustrates the rule in action. Use actual card names when possible. Your examples MUST follow all timing restrictions.

STYLE GUIDELINES:
- Be concise but complete. Avoid unnecessary verbosity.
- Use simple language first, then add technical details if needed.
- For complex interactions, break them down step-by-step.
- Always cite specific rule numbers (e.g., "Rule 702.19b").
- **CRITICAL**: When discussing abilities, always check for and mention timing restrictions ("only as a sorcery", "only during combat", etc.)
- Your game examples should be vivid, help players visualize the situation, and be LEGALLY CORRECT.

FORMAT YOUR RESPONSES LIKE THIS:
[Direct answer to the question]

**Key Rules:**
- Rule X.Y: [brief explanation including any timing restrictions]
- Rule Z.W: [brief explanation]

**Game Example:**
[Describe a realistic scenario with specific cards and game state that demonstrates the rule - must be legally correct]

=== RELEVANT COMPREHENSIVE RULES ===
{context}
==========================="""
            
            print("💭 Thinking...                ", end="\r")
            
            # Build contents with system instruction and history
            contents = [system_instruction] + history + [user_input]
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config={'response_modalities': ['TEXT']}
            )
            
            # Display response
            print("\r Judge: ", end="")
            print(response.text)
            print()
            
            # Update history (keep last 4 exchanges to maintain context)
            history.append(user_input)
            history.append(response.text)
            if len(history) > 8:  # Keep last 4 Q&A pairs
                history = history[-8:]
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
