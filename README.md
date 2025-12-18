# 🔮 MTG Rulebook AI Judge

> [!IMPORTANT]
> **WORK IN PROGRESS**: This project is currently under active development. Features and documentation may change frequently.

An intelligent Magic: The Gathering rules assistant powered by **Retrieval-Augmented Generation (RAG)**. This project uses **Groq (Llama 3.3 70B)** for state-of-the-art reasoning and semantic search for high-speed, accurate rules lookup.

## 🚀 Features

- **Expert Level Accuracy**: Emulates a Level 3 MTG Judge with clear, concise, and legally correct answers.
- **RAG Architecture**: Processes the entire Comprehensive Ruleset by indexing it into semantic chunks, allowing for fast and relevant context retrieval.
- **Vivid Game Examples**: Every answer includes a concrete game scenario with specific card names to illustrate the rules.
- **System Keychain Integration**: Securely stores your Groq API key using `keyring`.
- **Dual-Mode Intelligence**: Choose between a fast 'Normal' brain (8B) for simple queries and an 'Elite' smart brain (70B) for complex rules interactions.
- **High Throughput**: Capable of ~60+ Questions Per Minute (QPM) on the 8B model.

## 📊 Performance & Limits

Based on tests using Groq's high-speed inference:
- **Average Response Time**: ~1-3 seconds.
- **Measured Throughput**: Up to 60+ Questions Per Minute (QPM) depending on rate limits.
- **Recommended Speed**: Stay within Groq's free tier RPM (Rate Per Minute) limits.

> [!NOTE]
> This project now features **Dual-Mode Selection**:
> - **Normal (8B)**: Llama 3.1 8B Instant. Lightning fast and has a high daily quota. Perfect for 90% of MTG questions.
> - **Smart (70B)**: Llama 3.3 70B Versatile. GPT-4 level intelligence for the most complex "Layer" or interaction questions. Limited by a daily quota on the free tier.

## 🛠️ Architecture

The system operates in two main phases:

1.  **Indexing (`src/indexer.py`)**:
    - Parses the `MagicCompRules.txt` into logical rule sections.
    - Generates vector embeddings for each chunk using `SentenceTransformer ('all-MiniLM-L6-v2')`.
    - Saves the index for fast lookup.

2.  **Querying (`src/main.py`)**:
    - Uses semantic search to find the top 50 most relevant rule chunks for a user's question.
    - Constructs a rich context for the **Llama 3.3 70B** model.
    - Maintains a short conversation history for contextual follow-up questions.

## 📋 Prerequisites

- Python 3.8+
- A Groq API Key (get one for free at [Groq Console](https://console.groq.com/keys))

## ⚙️ Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AleVas-Elly/MTGjudgeAI.git
   cd MTGjudgeAI
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # OR
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Add the MTG Comprehensive Rules**:
   - Download `MagicCompRules.txt` from [Wizards of the Coast](https://magic.wizards.com/en/rules)
   - Place it in the `data/` folder (the folder will be created automatically)

5. **Initialize the rules index**:
   ```bash
   python src/indexer.py
   ```

## 🎮 Usage

**Important**: Always activate the virtual environment before running the app:
```bash
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows
```

Then run the main application:
```bash
python src/main.py
```

On the first run, you will be prompted to paste your Gemini API key. It will be saved securely to your system's keychain for future use.

## 📄 License

This project is for educational purposes. Magic: The Gathering is a trademark of Wizards of the Coast LLC.
