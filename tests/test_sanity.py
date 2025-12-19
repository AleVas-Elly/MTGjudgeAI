
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Simple smoke test to ensure modules import correctly."""
    from src.cli import MTGJudgeCLI
    from backend.app.core.config import SCRYFALL_SEARCH_URL
    from backend.app.services.llm import LLMService

    assert MTGJudgeCLI is not None
    assert SCRYFALL_SEARCH_URL is not None
    assert LLMService.VALID_INTENTS is not None
    assert "market" in LLMService.VALID_INTENTS
