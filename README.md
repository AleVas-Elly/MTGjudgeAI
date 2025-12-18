# 🔮 MTG Rulebook AI Judge

An intelligent Magic: The Gathering rules assistant powered by **Retrieval-Augmented Generation (RAG)**. This project uses **Groq (Llama 3.3 70B)** for state-of-the-art reasoning and a semantic vector index for high-speed, accurate rules lookup.

## 🚀 Features

- **Expert Level Accuracy**: Emulates a Level 3 MTG Judge with clear, concise answers and official rule citations.
- **RAG Architecture**: Processes the entire Comprehensive Ruleset via a semantic vector index for relevant context retrieval.
- **Historical Card Dossiers**: Fetch all unique prints, rarity, artist info, and finishes for any card.
- **Real-Time Market Pricing**: Live price data in EUR (€), USD ($), and TIX pulled directly from Scryfall.
- **Official B&R Verification**: Features a background sync engine that parses the official Wizards of the Coast Banned & Restricted list to provide authoritative legality checks.
- **Modular Service Architecture**: Professional, decoupled codebase using service-oriented design for LLM, RAG, and data retrieval.
- **System Keychain Integration**: Securely stores your Groq API key using the system's native keychain.
- **Dual-Mode Intelligence**: 
    - **Fast (8B)**: Llama 3.1 8B Instant for rapid-fire rulings.
    - **Deep (70B)**: Llama 3.3 70B Versatile for complex logic and layer-based interactions.

## 📊 Performance & Limits

- **Inference Speed**: ~1-3 seconds per query via Groq's high-speed TPU/LPUs.
- **Semantic Search**: Sub-millisecond retrieval from the local vector index.

## 🛠️ Project Structure

The project follows a modular architecture for better maintainability:

- `src/services/`: Core logic for `LLM`, `RAG`, `Scryfall`, and `Legality`.
- `src/utils/`: Security (keychain) and I/O utilities.
- `src/config.py`: Centralized configuration for models, paths, and prompts.
- `src/cli.py`: Interactive command-line interface.
- `src/br_updater.py`: Automated web parser for official B&R lists.
- `src/indexer.py`: Rulebook embedding and indexing engine.

## ⚙️ Setup

1. **Clone and Install**:
   ```bash
   git clone https://github.com/AleVas-Elly/MTGjudgeAI.git
   cd MTGjudgeAI
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Prepare Data**:
   - Place `MagicCompRules.txt` in the `data/` folder.
   - Run the indexer: `python -m src.indexer`
   - Sync the B&R list: `python -m src.br_updater`

3. **Launch**:
   ```bash
   python -m src.main
   ```

On the first run, you will be prompted for your **Groq API Key**. It will be saved securely to your system keychain.

## 📄 License & Legal

This project is an unofficial fan tool. Magic: The Gathering is a trademark of Wizards of the Coast LLC.
