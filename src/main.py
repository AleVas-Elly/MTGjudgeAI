import os
from backend.app.utils.security import get_api_key
from backend.app.utils.io import ensure_data_dir
from backend.app.services.llm import LLMService
from backend.app.services.rag import RAGService
from backend.app.services.scryfall import CardService
from backend.app.services.legality import LegalityService
from backend.app.services.cardtrader import CardTraderService
from backend.app.services.market import MarketIntelligenceService
from src.cli import MTGJudgeCLI

def main():
    # Initialize environment
    ensure_data_dir()
    api_key = get_api_key()
    
    # Initialize services
    print("Initialising services...")
    llm = LLMService(api_key)
    rag = RAGService()
    cards = CardService()
    legality = LegalityService()
    cardtrader = CardTraderService()
    cardtrader = CardTraderService()
    market = MarketIntelligenceService(cardtrader)
    
    # Start Interface
    app = MTGJudgeCLI(llm, rag, cards, legality, cardtrader, market)
    app.start()

if __name__ == "__main__":
    main()
