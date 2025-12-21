# 🔮 MTG Rulebook AI Judge

> [!IMPORTANT]
> **EXPERT SYSTEM**: This assistant emulates a Level 3 MTG Judge using a high-performance **Orchestration & Critic** pattern. It is designed for both speed (8B) and absolute rules accuracy (70B).

An intelligent Magic: The Gathering rules assistant powered by **Retrieval-Augmented Generation (RAG)**. This project uses **Groq**'s high-speed inference to provide authoritative rulings, market intelligence, and historical card dossiers.

## 🚀 Core High-Performance Features

- **Dual-Model Intelligence**: 
    - **Orchestrator (70B)**: Always used for high-precision tasks like intent detection, card name extraction, and complex search query generation.
    - **Fast Generator (8B)**: Llama 3.1 8B performs the final response generation for sub-second latency.
- **The Critic Pattern**: Every response from the 8B model is automatically verified by a format validator. If sections are missing or the quality is low, the query is **automatically escalated** to the 70B model.
- **Cross-Intent Context Persistence**: The Judge remembers the card you are discussing across different turns—switch from rules analysis to price trends without repeating the card name.
- **Defensive Resource Management**: Implements character-based context truncation to stay within strict Tokens-Per-Minute (TPM) limits of free/low-tier API accounts.
- **Data Harvesting (Mining Gold)**: Automatically logs high-quality "Gold Standard" interactions (from 70B) to `logs/interactions.jsonl` for future native fine-tuning of smaller models.

## 🛠️ Project Structure

- `src/`: Core Application Logic
    - `services/`: Modular logic for LLM (Groq), RAG (Vector storage), Scryfall, Market, and Legality.
    - `cli.py`: Refactored interactive interface with specialized context handlers.
    - `config.py`: Centralized configuration for the "MTG Know-it-all Judge" persona and prompts.
- `scripts/`: Development & Maintenance
    - `run_benchmarks.py`: Automated quality control script to verify persona and format accuracy.
    - `data_setup.py`: Master script for environment preparation.
- `tests/`: Benchmark data and test cases.
- `logs/`: Continuous data harvesting for fine-tuning.

## ⚙️ Quick Start

1. **Clone the Project**:
   ```bash
   git clone https://github.com/AleVas-Elly/MTGjudgeAI.git
   cd MTGjudgeAI
   ```

2. **One-Command Setup**:
   Simply run this to create the environment, install dependencies, and initialize the rulebook data:
   ```bash
   make setup
   ```
   *(Or run `./setup.sh` if you don't have make)*

3. **Launch the Judge**:
   ```bash
   make run
   ```

4. **Run Quality Benchmarks**:
   ```bash
   make benchmark
   ```

On the first run, you will be prompted for your **Groq API Key**. It will be saved securely to your system keychain and won't be requested again.

## 📄 Vision & Roadmap
For details on the project's evolution (Phase 1-4), check [ROADMAP_VISION.txt](ROADMAP_VISION.txt) and the [MTG_RULEBOOK_GUIDE.md](MTG_RULEBOOK_GUIDE.md) for a comprehensive technical guide to the codebase.

---
*Disclaimer: This project is an unofficial fan tool. Magic: The Gathering is a trademark of Wizards of the Coast LLC.*
