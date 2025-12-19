import json
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.llm import LLMService
from src.services.rag import RAGService
from src.services.scryfall import CardService
from src.config import NORMAL_MODEL, SMART_MODEL, PROMPT_JUDGE
from src.utils.security import get_api_key

class BenchmarkRunner:
    def __init__(self):
        api_key = get_api_key()
        self.llm = LLMService(api_key)
        self.rag = RAGService()
        self.cards = CardService()
        
    def run_case(self, case):
        query = case['query']
        print(f"\n--- Testing Query: {query} ---")
        
        # 1. Card extraction (using 70B as per orchestrator pattern)
        card_names = self.llm.extract_cards(query)
        scryfall_data = self.cards.get_card_data(card_names)
        
        card_context = ""
        if scryfall_data:
            card_context = "CARD DATA (Source of Truth):\n"
            for card in scryfall_data:
                stats = ""
                if card.get('power') and card.get('toughness'):
                    stats = f" | P/T: {card['power']}/{card['toughness']}"
                elif card.get('loyalty'):
                    stats = f" | Loyalty: {card['loyalty']}"

                card_context += (
                    f"Name: {card['name']}\n"
                    f"Cost: {card.get('mana_cost', 'N/A')} | Type: {card.get('type_line', 'N/A')}{stats}\n"
                    f"Oracle: {card.get('oracle_text', 'No oracle text')}\n"
                )
                if card.get('rulings'):
                    # Truncate rulings to keep context small
                    rulings = card['rulings'][:8]
                    card_context += "Official Rulings (Truncated):\n" + "\n".join([f"- {r}" for r in rulings]) + "\n"
                card_context += "-------------------\n"

        # 2. Rule retrieval (Use 10 chunks as per user config, but truncate for length)
        chunks = self.rag.retrieve(query)
        rules_text_list = []
        current_len = 0
        for c in chunks:
            chunk_str = f"[{c['rule_num']}] {c['text']}\n"
            if current_len + len(chunk_str) > 10000: # Defensive cap
                break
            rules_text_list.append(chunk_str)
            current_len += len(chunk_str)
        rules_context = "COMPREHENSIVE RULES:\n" + "".join(rules_text_list)
        
        # 3. Get Completion (8B)
        force_truth = "\n\nCRITICAL: EXTREME PRIORITY GIVEN TO 'CARD DATA (Source of Truth)'. USE ONLY PROVIDED TEXT."
        system_instruction = f"{PROMPT_JUDGE}\n\n{card_context}\n\n{rules_context}{force_truth}"
        messages = [{"role": "system", "content": system_instruction}, {"role": "user", "content": query}]
        
        response = self.llm.get_completion(NORMAL_MODEL, messages)
        
        # Phase 2 Critic Escalation (Benchmark also tests this)
        if NORMAL_MODEL in str(NORMAL_MODEL): # Always True, just to match cli.py structure
            is_valid, _ = self.llm.validate_format(response)
            if not is_valid and "Error" not in response:
                print("🕵️ Critic: Format invalid. Escalating to Deep (70B)...")
                response = self.llm.get_completion(SMART_MODEL, messages)
        
        
        # 4. Validate
        is_valid, missing = self.llm.validate_format(response)
        
        if is_valid:
            print("✅ PASS: Correct format detected.")
        else:
            print(f"❌ FAIL: Missing sections: {', '.join(missing)}")
            print("Response Sample:", response[:200] + "...")
            
        return is_valid

def main():
    test_file = "tests/test_cases.json"
    if not os.path.exists(test_file):
        print(f"Error: {test_file} not found.")
        return

    with open(test_file, 'r') as f:
        cases = json.load(f)

    runner = BenchmarkRunner()
    results = []
    
    print(f"🚀 Starting Benchmark on {len(cases)} cases...")
    for case in cases:
        results.append(runner.run_case(case))
        
    pass_count = sum(results)
    print(f"\n{'='*30}")
    print(f"BENCHMARK COMPLETE")
    print(f"Passed: {pass_count}/{len(cases)}")
    print(f"{'='*30}")

if __name__ == "__main__":
    main()
