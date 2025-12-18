import os
from src.utils.security import get_api_key
from src.utils.io import ensure_data_dir
from src.services.llm import LLMService
from src.services.rag import RAGService
from src.services.scryfall import CardService
from src.services.legality import LegalityService
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
    
    # Start Interface
    app = MTGJudgeCLI(llm, rag, cards, legality)
    app.start()

if __name__ == "__main__":
    main()
