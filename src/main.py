import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys
import keyring
import pickle
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import numpy as np
import requests
import json

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


def extract_card_names(client, user_input, history=[]):
    """
    Uses a fast LLM call to extract potential Magic card names from the user query.
    Returns a list of unique card names.
    """
    system_prompt = """You are a MTG card name extractor.
    Identify any potential Magic: The Gathering card names in the user's message.
    Return ONLY a JSON list of strings (e.g. ["Blood Moon", "Urza's Saga"]).
    If no cards are found, return [].
    Do not explain anything."""
    
    messages = [{"role": "system", "content": system_prompt}]
    # Optional: add history for context, but keep it minimal to save tokens
    if history:
        messages.append({"role": "user", "content": f"Previous context for pronoun resolution: {history[-2:]}"})
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = client.chat.completions.create(
            model=NORMAL_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=100
        )
        content = response.choices[0].message.content.strip()
        # Clean up any markdown code blocks
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        
        cards = json.loads(content)
        return list(set(cards)) # Unique names only
    except:
        return []

def fetch_scryfall_data(card_names):
    """
    Fetches official Oracle text, rulings, and metadata from Scryfall API.
    """
    card_data = []
    base_url = "https://api.scryfall.com/cards/named"
    
    for name in card_names:
        try:
            # Get card details
            resp = requests.get(base_url, params={"exact": name})
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            card_info = {
                "name": data.get("name"),
                "mana_cost": data.get("mana_cost", "N/A"),
                "type_line": data.get("type_line", "N/A"),
                "oracle_text": data.get("oracle_text", "N/A"),
                "power": data.get("power"),
                "toughness": data.get("toughness"),
                "loyalty": data.get("loyalty"),
                "artist": data.get("artist", "N/A"),
                "set_name": data.get("set_name", "N/A"),
                "rarity": data.get("rarity", "N/A"),
                "rulings": []
            }
            
            # Fetch rulings
            rulings_url = data.get("rulings_uri")
            if rulings_url:
                r_resp = requests.get(rulings_url)
                if r_resp.status_code == 200:
                    r_data = r_resp.json()
                    card_info["rulings"] = [r.get("comment") for r in r_data.get("data", [])]
            
            card_data.append(card_info)
        except:
            continue
            
    return card_data

def fetch_card_versions(card_name):
    """
    Fetches all unique prints of a card from Scryfall Search API.
    Returns: list of dicts with printing details.
    """
    versions = []
    # Search for exactly this card name, reporting all unique prints
    query = f'!"{card_name}"'
    url = "https://api.scryfall.com/cards/search"
    params = {
        "q": query,
        "unique": "prints",
        "order": "released",
        "dir": "asc"
    }
    
    try:
        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        for item in data.get("data", [])[:30]: # Limit to 30 versions to avoid token bloat
            versions.append({
                "set_name": item.get("set_name"),
                "released_at": item.get("released_at"),
                "collector_number": item.get("collector_number"),
                "artist": item.get("artist"),
                "price_eur": item.get("prices", {}).get("eur", "N/A")
            })
    except:
        pass
        
    return versions

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

def get_query_intent(client, query, history=[], last_intent=None):
    """
    Uses an LLM pass to classify the user's intent.
    Returns: 'rules', 'meta', 'off_topic', or 'clarify'
    """
    system_prompt = f"""You are an intent classifier for an MTG Rulebook AI assistant.
    Analyze the user's latest query and classify it into ONE of these categories:
    - rules: A specific question about Magic: The Gathering rules, card interactions, or tournament procedures.
    - versions: Requests to see all printings, sets, versions, or prices of a specific card.
    - meta: Questions about the AI bot itself, how it works, or help/instructions.
    - off_topic: General conversation, small talk, or questions about non-Magic subjects.
    - clarify: The query is MTG-related but too vague.

    EXAMPLES:
    - "What is the penalty for slow play?" -> rules
    - "Show me all versions of Lightning Bolt" -> versions
    - "How much is Murktide Regent?" -> versions
    - "Wait, what sets was Black Lotus in?" -> versions
    - "Tell me about yourself" -> meta
    - "What's the best pizza?" -> off_topic

    CONTEXT SENSITIVITY:
    - If the user uses pronouns (it, that, this, those) and the history contains an MTG topic, classify as 'rules'.
    - If the user explicitly changes the subject (e.g., "Enough about Magic, what's the weather?"), classify as 'off_topic'.
    - Prioritize the CURRENT query over the history.

    Return ONLY a single word: rules, meta, off_topic, or clarify. No explanation.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Include history for context
    if history:
        # Format history as a simple string to save tokens
        hist_str = ""
        for i in range(0, len(history), 2):
            if i < len(history): hist_str += f"User: {history[i]}\n"
            if i+1 < len(history): hist_str += f"Assistant: {history[i+1][:100]}...\n"
        messages.append({"role": "user", "content": f"CONVERSATION HISTORY:\n{hist_str}"})
    
    messages.append({"role": "user", "content": f"CURRENT QUERY: {query}"})
    
    try:
        response = client.chat.completions.create(
            model=NORMAL_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=10
        )
        prediction = response.choices[0].message.content.lower().strip()
        # Clean up any punctuation
        prediction = "".join(c for c in prediction if c.isalpha())
        
        if prediction in ["rules", "meta", "off_topic", "clarify", "versions"]:
            return prediction
        return "off_topic" # Safe default
    except:
        return "rules" # Use RAG as fallback to be safe


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
            intent = get_query_intent(client, user_input, history=history, last_intent=last_intent)
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
                # ... rest of off-topic ...
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

            elif intent == "clarify":
                print(f"Using {model_display} (Clarification)...")
                clarify_system = """You are an MTG Level 3 Judge. The user's question is MTG-related but too vague, ambiguous, or lacks context (e.g. they said "what happens?" but didn't name a card or situation).
                Politely ask the user for the specific details you need to provide an accurate ruling. 
                Be professional and helpful. Max 2 sentences."""
                
                messages = [{"role": "system", "content": clarify_system}]
                # Add history
                for i in range(0, len(history), 2):
                    if i < len(history): messages.append({"role": "user", "content": history[i]})
                    if i + 1 < len(history): messages.append({"role": "assistant", "content": history[i+1]})
                messages.append({"role": "user", "content": user_input})

                print("💭 Thinking...                ", end="\r")
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=0.5,
                    max_tokens=150
                )
                final_response = response.choices[0].message.content

            elif intent == "versions":
                print(f"Using {model_display} (History)...")
                print("🔍 Searching all card versions...", end="\r")
                
                # Identify the card name first
                potential_cards = extract_card_names(client, user_input, history=history)
                if not potential_cards:
                    # Fallback to rules if extraction fails
                    intent = "rules" 
                else:
                    card_name = potential_cards[0] # Use the primary card
                    versions_data = fetch_card_versions(card_name)
                    
                    if not versions_data:
                        final_response = f"I couldn't find any historical printings for '{card_name}' on Scryfall."
                    else:
                        # Build a formatting prompt
                        version_context = f"All versions of {card_name}:\n"
                        for v in versions_data:
                            version_context += f"- Set: {v['set_name']} ({v['released_at'][:4]}) | No. {v['collector_number']} | Artist: {v['artist']} | Price: {v['price_eur']}€\n"
                        
                        system_msg = """You are an MTG Historian. The user wants a list of all versions of a card.
                        Format the provided data into a clean, easy-to-read list or table.
                        Include the Set Name, Year, Collector Number, Artist, and Price in Euro.
                        Be professional and concise."""
                        
                        messages = [
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": version_context}
                        ]
                        
                        print("💭 Formatting response...      ", end="\r")
                        response = client.chat.completions.create(
                            model=selected_model,
                            messages=messages,
                            temperature=0.3,
                            max_tokens=1000
                        )
                        final_response = response.choices[0].message.content

            elif intent == "rules":
                print(f"Using {model_display}...")
                
                # 2. Card Name Extraction & Scryfall Fetch
                print("🔍 Identifying cards and fetching data...", end="\r")
                potential_cards = extract_card_names(client, user_input, history=history)
                scryfall_data = fetch_scryfall_data(potential_cards)
                
                card_context = ""
                if scryfall_data:
                    card_context = "\n=== CARD DATA FROM SCRYFALL ===\n"
                    for card in scryfall_data:
                        card_context += f"Name: {card['name']}\n"
                        card_context += f"Mana Cost: {card['mana_cost']} | Type: {card['type_line']}\n"
                        if card['power']: card_context += f"P/T: {card['power']}/{card['toughness']}\n"
                        if card['loyalty']: card_context += f"Loyalty: {card['loyalty']}\n"
                        card_context += f"Oracle: {card['oracle_text']}\n"
                        card_context += f"Artist: {card['artist']} | Set: {card['set_name']} ({card['rarity']})\n"
                        if card['rulings']:
                            card_context += "Rulings:\n"
                            for ruling in card['rulings'][:5]: # Top 5 rulings to save space
                                card_context += f" - {ruling}\n"
                        card_context += "\n"
                    card_context += "===============================\n"

                print("🔍 Finding relevant rules...              ", end="\r")
                # 3. Rules Retrieval (RAG)
                relevant_chunks = retrieve_relevant_chunks(
                    user_input, 
                    index_data, 
                    embedding_model,
                    history=history,
                    top_k=TOP_K_CHUNKS
                )
                
                # Build context from relevant chunks
                rules_context = "\n\n".join([
                    f"[Rule {chunk['rule_num']}]\n{chunk['text']}" 
                    for chunk in relevant_chunks
                ])
                
                # System instruction with retrieved context
                system_instruction = f"""You are an expert Magic: The Gathering Level 3 Judge with exceptional teaching skills. Your mission is to provide clear, concise, and practical answers to rules questions using the official Comprehensive Rules and specific Card Data provided.
    
    CRITICAL: Pay extremely close attention to timing restrictions, activation costs, and conditions in the rules. Many abilities have restrictions like "Activate only as a sorcery" or "Activate only during combat" - these MUST be respected in your examples.
    
    {card_context}
    
    RESPONSE STRUCTURE:
    1. **Direct Answer** (1-2 sentences): Answer the question immediately and clearly.
    2. **Card Info** (required if card data exists): Briefly state the card name, artist, and set name for each card mentioned.
    3. **Key Rules** (bullet points): List only the most relevant rule citations with brief explanations. ALWAYS include timing restrictions if relevant.
    4. **Game Example** (required): End EVERY response with a concrete, realistic game scenario that illustrates the rule in action. Use actual card names when possible. Your examples MUST follow all timing restrictions.
    
    STYLE GUIDELINES:
    - Be concise but complete. Avoid unnecessary verbosity.
    - Use simple language first, then add technical details if needed.
    - For complex interactions, break them down step-by-step.
    - Always cite specific rule numbers (e.g., "Rule 702.19b").
    - **CRITICAL**: When discussing abilities, always check for and mention timing restrictions ("only as a sorcery", "only during combat", etc.)
    - Your game examples should be vivid, help players visualize the situation, and be LEGALLY CORRECT.
    - If card data is provided above, use that EXACT oracle text for your logic.
    
    FORMAT YOUR RESPONSES LIKE THIS:
    [Direct answer to the question]
    
    **Card Details:**
    [Name] - [Artist] - [Set Name]
    
    **Key Rules:**
    - Rule X.Y: [brief explanation including any timing restrictions]
    - Rule Z.W: [brief explanation]
    
    **Game Example:**
    [Describe a realistic scenario with specific cards and game state that demonstrates the rule - must be legally correct]
    
    === RELEVANT COMPREHENSIVE RULES ===
    {rules_context}
    ==========================="""
                
                # rules_context = ... (built above)
                
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
            print("\r" + " " * 50 + "\r", end="") # Clear line
            print("Judge: ", end="")
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
