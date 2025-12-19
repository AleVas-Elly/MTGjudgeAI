from functools import lru_cache
import os
from dotenv import load_dotenv

from backend.app.services.chat_controller import ChatController
from backend.app.services.llm import LLMService
from backend.app.services.rag import RAGService
from backend.app.services.scryfall import CardService
from backend.app.services.legality import LegalityService
from backend.app.services.cardtrader import CardTraderService
from backend.app.services.market import MarketIntelligenceService
import keyring

load_dotenv()

from backend.app.core.config import SERVICE_NAME, USERNAME

@lru_cache()
def get_chat_controller():
    # Retrieve Keys
    groq_api_key = os.getenv("GROQ_API_KEY") or keyring.get_password(SERVICE_NAME, USERNAME)
    cardtrader_token = os.getenv("CARDTRADER_TOKEN") or keyring.get_password(SERVICE_NAME, "cardtrader_api_key")

    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment or keyring.")

    # Initialize Services
    llm = LLMService(groq_api_key)
    rag = RAGService()
    cards = CardService()
    legality = LegalityService()
    # Market
    cardtrader = CardTraderService()
    # Stocks removed
    market = MarketIntelligenceService(cardtrader)

    return ChatController(llm, rag, cards, legality, cardtrader, market)
