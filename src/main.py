import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys
import keyring
import pickle
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import numpy as np

# Load environment variables (optional, for other configs)
load_dotenv()

RULEBOOK_PATH = 'data/MagicCompRules.txt'
INDEX_PATH = 'data/rulebook_index.pkl'
SERVICE_NAME = "mtg_rulebook_ai"
USERNAME = "groq_api_key"
TOP_K_CHUNKS = 10  # Reduced to stay within Groq's 12,000 TPM limit
SMART_MODEL = "llama-3.3-70b-versatile"
NORMAL_MODEL = "llama-3.1-8b-instant"

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
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("\n⚠️  Groq API Key not found in Keychain or environment.")
        print("You can get a free key from: https://console.groq.com/keys")
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

def retrieve_relevant_chunks(query, index_data, model, history=None, top_k=TOP_K_CHUNKS):
    """Retrieve the most relevant rule chunks, using history for context."""
    # Combine query with last user question for better context if it's a short question
    search_query = query
    if history and len(query.split()) < 5:
        # history is [user, assistant, user, assistant...]
        last_user_q = history[-2] if len(history) >= 2 else ""
        search_query = f"{last_user_q} {query}"
        
    # Generate query embedding
    query_embedding = model.encode([search_query])[0]
    
    # Calculate cosine similarity with all chunks
    chunk_embeddings = index_data['embeddings']
    similarities = np.dot(chunk_embeddings, query_embedding) / (
        np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top-k most similar chunks
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    relevant_chunks = [index_data['chunks'][i] for i in top_indices]
    return relevant_chunks

def get_query_intent(query, last_intent=None):
    """
    Simple intent classifier with context awareness.
    If the current query is very short or vague, and the last intent was 'rules',
    it leans towards 'rules' to allow follow-ups.
    """
    # Keywords that suggest a question about the bot/self
    meta_keywords = [
        'who are you', 'how do you work', 'what are you', 
        'what can you do', 'help', 'instructions', 'commands',
        'how does this work', 'about you', 'your name'
    ]
    
    q_lower = query.lower().strip()
    
    # Check for meta intent
    for keyword in meta_keywords:
        if keyword in q_lower:
            return "meta"
            
    # Keywords that suggest a question about Magic rules
    mtg_keywords = [
        'spell', 'cast', 'combat', 'creature', 'artifact', 'enchantment', 
        'land', 'graveyard', 'library', 'hand', 'exile', 'stack', 
        'priority', 'turn', 'phase', 'step', 'damage', 'life', 'counter', 
        'win', 'lose', 'commander', 'rule', 'trigger', 'ability', 'mana', 
        'tap', 'untap', 'block', 'attack', 'layer', 'state-based', 'effect', 
        'player', 'token', 'copy', 'protection', 'indestructible', 'flying',
        'cascade', 'scry', 'draw', 'discard', 'hand size', 'poison', 'planeswalker',
        'assistance', 'outside', 'infraction', 'penalty', 'warning', 'judge',
        'tournament', 'match', 'game state', 'interact', 'interaction',
        'explain', 'card', 'how', 'what', 'does', 'if'
    ]
    
    # Check for MTG terms
    for keyword in mtg_keywords:
        if keyword in q_lower:
            return "rules"
            
    # Context-aware follow-ups: if it's a follow-up-style question and the last intent was rules/meta, keep it
    follow_up_starters = ['how', 'what', 'and', 'why', 'can', 'does', 'if']
    is_follow_up = any(q_lower.startswith(s) for s in follow_up_starters)
    
    if (len(q_lower.split()) <= 12 or is_follow_up) and last_intent in ["rules", "meta"]:
        return last_intent
        
    # Default to off-topic if no keywords found and not a clear follow-up
    return "off_topic"


def main():
    print("🔮 MTG Rulebook AI Judge (RAG Edition) 🔮")
    print("------------------------------------------")
    
    # Ensure directory structure exists
    ensure_directories()
    
    # Setup
    api_key = get_api_key()
    client = Groq(api_key=api_key)
    
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
    last_intent = None

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue

            # Model Selection
            print("\n🧠 Brain Level for this question?")
            print("[1] Normal (8B) - Fast & Saves quota")
            print("[2] Smart (70B) - Deep reasoning for complex rules")
            choice = input("Choice (1 or 2, default=1): ").strip()
            
            selected_model = SMART_MODEL if choice == '2' else NORMAL_MODEL
            model_display = "Smart (70B) 🧠" if choice == '2' else "Normal (8B) ⚡"
            
            # 1. Intent Classification
            intent = get_query_intent(user_input, last_intent=last_intent)
            last_intent = intent
            
            final_response = ""
            
            if intent == "meta":
                print(f"Using {model_display} (General)...")
                system_msg = "You are the MTG Rulebook AI Judge. When users ask about you or how you work, explain that you use a Retrieval-Augmented Generation (RAG) system to search the official Magic Comprehensive Rules. Be friendly and helpful."
                
                messages = [{"role": "system", "content": system_msg}]
                # Add history
                for i in range(0, len(history), 2):
                    if i < len(history): messages.append({"role": "user", "content": history[i]})
                    if i + 1 < len(history): messages.append({"role": "assistant", "content": history[i+1]})
                messages.append({"role": "user", "content": user_input})

                print("💭 Thinking...                ", end="\r")
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=300
                )
                final_response = response.choices[0].message.content

            elif intent == "off_topic":
                print(f"Using {model_display} (Off-topic)...")
                off_topic_system = """You are a strict MTG Level 3 Judge. The user asked a non-Magic question. 
                Refuse to answer with a hilarious, ultra-short MTG tournament metaphor. 
                (e.g. 'Warning for Outside Assistance! This is a Magic match.') 
                CRITICAL: Max 1-2 SHORT sentences. Be extremely punchy. Use Judge terms like Warning, Game Loss, or DQ."""
                
                messages = [{"role": "system", "content": off_topic_system}]
                # Add history
                for i in range(0, len(history), 2):
                    if i < len(history): messages.append({"role": "user", "content": history[i]})
                    if i + 1 < len(history): messages.append({"role": "assistant", "content": history[i+1]})
                messages.append({"role": "user", "content": user_input})

                print("💭 Thinking...                ", end="\r")
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=50
                )
                final_response = response.choices[0].message.content

            else:
                # RULES INTENT
                print(f"Using {model_display}...")
                print("🔍 Finding relevant rules...", end="\r")
                
                # 2. Rules Retrieval (RAG)
                relevant_chunks = retrieve_relevant_chunks(
                    user_input, 
                    index_data, 
                    embedding_model,
                    history=history,
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
                
                messages = [{"role": "system", "content": system_instruction}]
                # Add conversation history
                for i in range(0, len(history), 2):
                    if i < len(history): messages.append({"role": "user", "content": history[i]})
                    if i + 1 < len(history): messages.append({"role": "assistant", "content": history[i+1]})
                messages.append({"role": "user", "content": user_input})
                
                # Call Groq API
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2048
                )
                final_response = response.choices[0].message.content

            # Display response
            print("\r Judge: ", end="")
            print(final_response)
            print()
            
            # Update history (keep last 4 exchanges to maintain context)
            history.append(user_input)
            history.append(final_response)
            if len(history) > 8:  # Keep last 4 Q&A pairs
                history = history[-8:]
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
