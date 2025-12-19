import json
from groq import Groq
from backend.app.core.config import NORMAL_MODEL, SMART_MODEL, PROMPT_INTENT

class LLMService:
    VALID_INTENTS = ["rules", "lookup", "meta", "off_topic", "clarify", "versions", "market", "retry"]

    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def classify_intent(self, query, history=[]):
        """Determines the user's intent."""
        messages = [{"role": "system", "content": PROMPT_INTENT}]
        if history:
            hist_str = ""
            for i in range(0, len(history), 2):
                if i < len(history): hist_str += f"User: {history[i]}\n"
                if i+1 < len(history): hist_str += f"Judge: {history[i+1][:100]}...\n"
            messages.append({"role": "user", "content": f"History:\n{hist_str}"})
        
        messages.append({"role": "user", "content": f"Query: {query}"})
        
        try:
            resp = self.client.chat.completions.create(
                model=SMART_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=10
            )
            prediction = resp.choices[0].message.content.lower().strip()
            prediction = "".join(c for c in prediction if c.isalpha() or c == '_')
            
            valid_intents = self.VALID_INTENTS
            for intent in valid_intents:
                if intent in prediction:
                    return intent
            return "rules"
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return "rules"

    def extract_cards(self, query, history=[]):
        """Extracts card names explicitly mentioned in the query.
        Does NOT resolve pronouns or context—only returns names physically in the query string.
        """
        prompt = """Identify MTG card names EXPLICITLY mentioned in the user's latest query.
        
        NEGATIVE CONSTRAINTS:
        - DO NOT return a name if it is not a substring of the query.
        - DO NOT resolve pronouns like 'it', 'that card', 'the first one', or 'this'.
        - DO NOT use information from the conversation history to infer card names.
        
        EXAMPLES:
        - Query: 'what is its price?' -> []
        - Query: 'Tell me about Black Lotus' -> ["Black Lotus"]
        - Query: 'How much for the first one?' -> []
        - Query: 'I was asking about Tundra earlier' -> ["Tundra"]
        
        Return ONLY a JSON list of strings. Empty list if none."""

        
        # We don't pass history to extraction to avoid the LLM getting confused 
        # about what is 'new' vs 'context'.
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Query: {query}"}
        ]
        
        try:
            resp = self.client.chat.completions.create(
                model=SMART_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=100
            )
            content = resp.choices[0].message.content.strip()
            if "[" in content and "]" in content:
                content = content[content.find("["):content.rfind("]")+1]
            return list(set(json.loads(content)))
        except Exception:
            return []

    def generate_search_query(self, query, history=[]):
        """Converts natural language into Scryfall search syntax."""
        from backend.app.core.config import PROMPT_SEARCH
        
        # Short-circuit for numeric selection
        if query.isdigit():
            return query

        messages = [{"role": "system", "content": PROMPT_SEARCH}]
        if history:
            messages.append({"role": "user", "content": f"Context: {history[-2:]}"})
        messages.append({"role": "user", "content": query})
        
        try:
            resp = self.client.chat.completions.create(
                model=SMART_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=100
            )
            result = resp.choices[0].message.content.strip()
            
            # Post-process: specific fixes
            # 1. If it starts with ! but has spaces and NO quotes, add them.
            if result.startswith("!") and " " in result and '"' not in result:
                # !Murktide Regent -> !"Murktide Regent"
                card_part = result[1:]
                result = f"!\"{card_part}\""
            
            return result
        except Exception:
            return query


    def should_show_prices(self, query):
        """Detects if the user is asking for pricing."""
        from backend.app.core.config import PROMPT_PRICE_DETECT
        messages = [
            {"role": "system", "content": PROMPT_PRICE_DETECT},
            {"role": "user", "content": query}
        ]
        try:
            resp = self.client.chat.completions.create(
                model=SMART_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=5
            )
            return "true" in resp.choices[0].message.content.lower()
        except Exception:
            return False

    def rewrite_query(self, query, history=[]):
        """Rewrites the query into a self-contained version using history."""
        from backend.app.core.config import PROMPT_REWRITER
        if not history:
            return query
            
        hist_str = ""
        # Use last 4 messages for context
        for i in range(max(0, len(history)-4), len(history), 2):
            if i < len(history): hist_str += f"User: {history[i]}\n"
            if i+1 < len(history): hist_str += f"Judge: {history[i+1][:100]}...\n"
            
        messages = [
            {"role": "system", "content": PROMPT_REWRITER},
            {"role": "user", "content": f"History:\n{hist_str}\n\nLast User Query: {query}"}
        ]
        
        try:
            resp = self.client.chat.completions.create(
                model=NORMAL_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=200
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return query

    def get_completion(self, model, messages, temperature=0.7, max_tokens=1000):
        """Generic completion wrapper."""
        try:
            resp = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"

    def validate_format(self, text):
        """Checks if the response follows the 4-section format (robustly)."""
        # We check for the keywords rather than exact emoji sequences to be robust
        required_keywords = ["CARD INFO", "ORACLE TEXT", "RULING", "GAMEPLAY SCENARIO"]
        text_upper = text.upper()
        missing = [kw for kw in required_keywords if kw not in text_upper]
        return len(missing) == 0, missing
