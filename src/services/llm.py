import json
from groq import Groq
from src.config import NORMAL_MODEL, PROMPT_INTENT

class LLMService:
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
                model=NORMAL_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=10
            )
            prediction = resp.choices[0].message.content.lower().strip()
            prediction = "".join(c for c in prediction if c.isalpha())
            
            valid_intents = ["rules", "meta", "off_topic", "clarify", "versions"]
            return prediction if prediction in valid_intents else "off_topic"
        except Exception:
            return "rules"

    def extract_cards(self, query, history=[]):
        """Extracts card names mentioned in the query."""
        prompt = """Identify MTG card names. Return ONLY a JSON list of strings. Empty list if none."""
        messages = [{"role": "system", "content": prompt}]
        if history:
            messages.append({"role": "user", "content": f"Context: {history[-2:]}"})
        messages.append({"role": "user", "content": query})
        
        try:
            resp = self.client.chat.completions.create(
                model=NORMAL_MODEL,
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
