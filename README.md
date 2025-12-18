# 🔮 MTG Rulebook AI Judge

> [!IMPORTANT]
> **WORK IN PROGRESS**: This project is currently under active development. Features and documentation may change frequently.

An intelligent Magic: The Gathering rules assistant powered by **Retrieval-Augmented Generation (RAG)**. This project uses Google Gemini for advanced reasoning and semantic search for high-speed, accurate rules lookup.

## 🚀 Features

- **Expert Level Accuracy**: Emulates a Level 3 MTG Judge with clear, concise, and legally correct answers.
- **RAG Architecture**: Processes the entire Comprehensive Ruleset by indexing it into semantic chunks, allowing for fast and relevant context retrieval.
- **Vivid Game Examples**: Every answer includes a concrete game scenario with specific card names to illustrate the rules.
- **System Keychain Integration**: Securely stores your Gemini API key using `keyring`.
- **High Throughput**: Capable of ~5.6 Questions Per Minute (QPM) while maintaining more than good accuracy via Gemini 2.5 Flash.

## 📊 Performance & Limits

Based on recent load tests using 10 complex MTG rules questions:
- **Average Response Time**: ~10.7 seconds.
- **Measured Throughput**: 5.61 Questions Per Minute (QPM).
- **Recommended Speed**: 5 RPM (to stay within free tier rate limits).

> [!NOTE]
> This project uses **Gemini 2.5 Flash**, which offers "Adaptive Thinking" and improved accuracy over version 1.5. If you hit rate limits frequently, the application is designed to handle ~5 requests per minute.

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
