# 🔮 MTG Rulebook AI Judge

An intelligent Magic: The Gathering rules assistant powered by **Retrieval-Augmented Generation (RAG)**. This project uses Google Gemini for advanced reasoning and semantic search for high-speed, accurate rules lookup.

## 🚀 Features

- **Expert Level Accuracy**: Emulates a Level 3 MTG Judge with clear, concise, and legally correct answers.
- **RAG Architecture**: Processes the entire Comprehensive Ruleset by indexing it into semantic chunks, allowing for fast and relevant context retrieval.
- **Vivid Game Examples**: Every answer includes a concrete game scenario with specific card names to illustrate the rules.
- **System Keychain Integration**: Securely stores your Gemini API key using `keyring`.
- **High Throughput**: Optimized for 5-10 questions per minute by only sending relevant rule chunks to the AI.

## 🛠️ Architecture

The system operates in two main phases:

1.  **Indexing (`src/indexer.py`)**:
    - Parses the `MagicCompRules.txt` into logical rule sections.
    - Generates vector embeddings for each chunk using `SentenceTransformer ('all-MiniLM-L6-v2')`.
    - Saves the index for fast lookup.

2.  **Querying (`src/main.py`)**:
    - Uses semantic search to find the top 50 most relevant rule chunks for a user's question.
    - Constructs a rich context for the Gemini 1.5 Flash model.
    - Maintains a short conversation history for contextual follow-up questions.

## 📋 Prerequisites

- Python 3.8+
- A Google Gemini API Key (get one for free at [AI Studio](https://aistudio.google.com/app/apikey))

## ⚙️ Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd "MTG Rulebook"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the rules index**:
   *Ensure you have `data/MagicCompRules.txt` in the project root.*
   ```bash
   python src/indexer.py
   ```

## 🎮 Usage

Run the main application:
```bash
python src/main.py
```

On the first run, you will be prompted to paste your Gemini API key. It will be saved securely to your system's keychain for future use.

## 📄 License

This project is for educational purposes. Magic: The Gathering is a trademark of Wizards of the Coast LLC.
