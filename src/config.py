import os

# Project Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RULEBOOK_PATH = os.path.join(DATA_DIR, "MagicCompRules.txt")
INDEX_PATH = os.path.join(DATA_DIR, "rulebook_index.pkl")
BR_FILE = os.path.join(DATA_DIR, "banned_restricted.json")

# API Configuration
SERVICE_NAME = "mtg_rulebook_ai"
USERNAME = "groq_api_key"
RULES_DOWNLOAD_URL = "https://media.wizards.com/2025/downloads/MagicCompRules%2020251114.txt"
SCRTYFALL_NAMED_URL = "https://api.scryfall.com/cards/named"
SCRTYFALL_SEARCH_URL = "https://api.scryfall.com/cards/search"
BR_URL = "https://magic.wizards.com/en/banned-restricted-list"

# Model Configuration
SMART_MODEL = "llama-3.3-70b-versatile"
NORMAL_MODEL = "llama-3.1-8b-instant"
TOP_K_CHUNKS = 10

# AI Prompts
PROMPT_INTENT = """Analyze the query and classify into: rules, versions, meta, off_topic, or clarify.
Return ONLY the category name. No punctuation."""

PROMPT_OFF_TOPIC = """Strict MTG Level 3 Judge. Cleverly refuse non-Magic questions.
Always state you are MTG-focused. 1-2 sentences."""

PROMPT_CLARIFY = """Professional MTG Judge. Politely request missing context (cards, phase, state). 2 sentences max."""

PROMPT_HISTORIAN = """MTG Historian. Provide accurate version data and pricing.
Verify legality against official WotC B&R data provided."""

PROMPT_JUDGE = """Expert MTG Judge. Answer rules questions with official citations and game examples.
Follow timing restrictions and Oracle text strictly."""
