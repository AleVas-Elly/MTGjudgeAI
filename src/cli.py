import sys
from src.config import SMART_MODEL, NORMAL_MODEL, PROMPT_OFF_TOPIC, PROMPT_CLARIFY, PROMPT_HISTORIAN, PROMPT_JUDGE

class MTGJudgeCLI:
    def __init__(self, llm_service, rag_service, card_service, legality_service):
        self.llm = llm_service
        self.rag = rag_service
        self.cards = card_service
        self.legality = legality_service
        self.history = []

    def start(self):
        print("\n=== MTG Rulebook AI Judge ===")
        print("Authoritative rulings and card data.\n")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Session ended.")
                    break
                
                if not user_input:
                    continue

                # Model Selection
                print("[1] Fast (8B) [2] Deep (70B)")
                choice = input("Brain Level (default 1): ").strip()
                selected_model = SMART_MODEL if choice == '2' else NORMAL_MODEL
                
                # Intent
                intent = self.llm.classify_intent(user_input, self.history)
                
                response = ""
                if intent == "meta":
                    response = self._handle_meta(user_input, selected_model)
                elif intent == "off_topic":
                    response = self._handle_off_topic(user_input, selected_model)
                elif intent == "clarify":
                    response = self._handle_clarify(user_input, selected_model)
                elif intent == "versions":
                    response = self._handle_versions(user_input, selected_model)
                else: # rules
                    response = self._handle_rules(user_input, selected_model)

                print(f"\nJudge: {response}")
                
                # Update history
                self.history.extend([user_input, response])
                if len(self.history) > 8:
                    self.history = self.history[-8:]

            except KeyboardInterrupt:
                print("\nSession ended.")
                break
            except Exception as e:
                print(f"\nRuntime Error: {e}")

    def _handle_meta(self, query, model):
        system_msg = "You are the MTG Rulebook AI Judge. Explain your capabilities: answering rules, listing card versions, providing market prices, and checking format legality."
        messages = [{"role": "system", "content": system_msg}]
        return self.llm.get_completion(model, messages + [{"role": "user", "content": query}])

    def _handle_off_topic(self, query, model):
        messages = [{"role": "system", "content": PROMPT_OFF_TOPIC}, {"role": "user", "content": query}]
        return self.llm.get_completion(model, messages)

    def _handle_clarify(self, query, model):
        messages = [{"role": "system", "content": PROMPT_CLARIFY}, {"role": "user", "content": query}]
        return self.llm.get_completion(model, messages)

    def _handle_versions(self, query, model):
        card_names = self.llm.extract_cards(query, self.history)
        if not card_names:
            return "Please provide a specific card name to check versions."
        
        card_name = card_names[0]
        versions = self.cards.get_card_versions(card_name)
        if not versions:
            return f"No official records found for '{card_name}'."

        legality_status = self.legality.check_legality(card_name)
        
        context = f"Data for: {card_name}\n\n"
        for v in versions:
            context += f"Set: {v['set_name']} | Price: {v['prices']['eur']} EUR | {v['prices']['usd']} USD\n"
        
        if legality_status:
            context += "\nOFFICIAL B&R STATUS:\n" + "\n".join(legality_status)

        messages = [
            {"role": "system", "content": PROMPT_HISTORIAN},
            {"role": "user", "content": f"Query: {query}\n\n{context}"}
        ]
        return self.llm.get_completion(model, messages, max_tokens=1500)

    def _handle_rules(self, query, model):
        card_names = self.llm.extract_cards(query, self.history)
        scryfall_data = self.cards.get_card_data(card_names)
        
        card_context = ""
        if scryfall_data:
            card_context = "CARD DATA:\n"
            for card in scryfall_data:
                card_context += f"Name: {card['name']} | Oracle: {card['oracle_text']}\n"
                if card['rulings']:
                    card_context += "Rulings:\n" + "\n".join([f"- {r}" for r in card['rulings'][:3]]) + "\n"

        chunks = self.rag.retrieve(query, self.history)
        rules_context = "COMPREHENSIVE RULES:\n" + "\n".join([f"[{c['rule_num']}] {c['text']}" for c in chunks])

        system_instruction = f"{PROMPT_JUDGE}\n\n{card_context}\n\n{rules_context}"
        
        messages = [{"role": "system", "content": system_instruction}]
        for i in range(0, len(self.history), 2):
            messages.append({"role": "user", "content": self.history[i]})
            messages.append({"role": "assistant", "content": self.history[i+1]})
        messages.append({"role": "user", "content": query})

        return self.llm.get_completion(model, messages)
