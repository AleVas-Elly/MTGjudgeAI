import sys
import os
import keyring
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.llm import LLMService
from src.services.scryfall import CardService
from src.services.rag import RAGService
from src.services.legality import LegalityService
from src.services.cardtrader import CardTraderService
from src.services.market import MarketIntelligenceService
from src.cli import MTGJudgeCLI
from backend.app.core.config import NORMAL_MODEL, SMART_MODEL

def get_api_key():
    service_name = "mtg_rulebook_ai"
    username = "groq_api_key"
    api_key = keyring.get_password(service_name, username)
    if not api_key:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
    return api_key

def main():
    api_key = get_api_key()
    if not api_key:
        print("Error: No Groq API key found.")
        return

    # Initialize services
    llm = LLMService(api_key)
    scryfall = CardService()
    rag = RAGService()
    legality = LegalityService()
    cardtrader = CardTraderService()
    market = MarketIntelligenceService(cardtrader)
    
    cli = MTGJudgeCLI(llm, rag, scryfall, legality, cardtrader, market)

    print("\n--- Verifying Context Persistence ---")
    
    # 1. Lackey vs Guide Test
    print("\nQuery: 'Tell me about Goblin Lackey'")
    resp1 = cli._handle_rules("Tell me about Goblin Lackey", NORMAL_MODEL)
    print(f"Cards in context: {cli.active_context['cards']}")
    
    print("\nQuery: 'What is its price?'")
    resp2 = cli._handle_versions("What is its price?", NORMAL_MODEL)
    print(f"Cards in context: {cli.active_context['cards']}")
    if "Goblin Lackey" in resp2 or ("Tundra" not in resp2 and cli.active_context['cards'] == ["Goblin Lackey"]):
        print("✅ PASS: Correct card in context (Lackey)")
    else:
        print("❌ FAIL: Wrong card or no card in context")


    print("\nQuery: 'Tell me about Goblin Guide'")
    resp3 = cli._handle_rules("Tell me about Goblin Guide", NORMAL_MODEL)
    print(f"Cards in context: {cli.active_context['cards']}")
    
    print("\nQuery: 'What is its price?'")
    resp4 = cli._handle_versions("What is its price?", NORMAL_MODEL)
    print(f"Cards in context: {cli.active_context['cards']}")
    if "Goblin Guide" in resp4:
        print("✅ PASS: Correct card in context (Guide)")
    else:
        print("❌ FAIL: Wrong card or no card in context")

    print("\n--- Verifying Pricing Flow ---")
    
    print("\nQuery: 'What is the price of Tundra?'")
    resp5 = cli._handle_versions("What is the price of Tundra?", NORMAL_MODEL)
    print(f"Initial Report Output Snippet:\n{resp5[:200]}...")
    
    if "🛒 STORE SEARCH:" in resp5 and "Cardmarket" in resp5 and "Cardtrader" in resp5:
        print("✅ PASS: Store search links found in initial report.")
    else:
        print("❌ FAIL: Store search links missing or misformatted.")

    print("\nSimulating selecting version '1'...")
    resp6 = cli._handle_versions("1", NORMAL_MODEL)
    print(f"Deep Dive Output Snippet:\n{resp6[:400]}...")
    
    if "Tundra | Limited Edition Alpha" in resp6 and "Lowest Price" in resp6 and "[Buy on Cardmarket]" in resp6:
        print("✅ PASS: Concise report successfully generated with specific purchase links.")
    else:
        print("❌ FAIL: Concise report missing key sections or specific links.")

if __name__ == "__main__":
    main()
