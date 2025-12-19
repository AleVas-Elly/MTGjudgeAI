import sys
from backend.app.core.config import SMART_MODEL, NORMAL_MODEL, PROMPT_OFF_TOPIC, PROMPT_CLARIFY, PROMPT_JUDGE
from backend.app.utils.market_links import get_cm_search_link, get_cm_version_link, get_ct_search_link, get_ct_version_link


class MTGJudgeCLI:
    def __init__(self, llm_service, rag_service, card_service, legality_service, cardtrader_service, market_service):
        self.llm = llm_service
        self.rag = rag_service
        self.cards = card_service
        self.legality = legality_service
        self.cardtrader = cardtrader_service
        self.market = market_service
        self.history = []
        self.active_context = {"cards": [], "intent": None}

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
                
                # 2. Intent
                intent = self.llm.classify_intent(user_input, self.history)
                print(f"🎯 Intent: {intent}")
                
                response = ""
                if intent == "meta":
                    response = self._handle_meta(user_input, selected_model)
                elif intent == "off_topic":
                    response = self._handle_off_topic(user_input, selected_model)
                elif intent == "clarify":
                    response = self._handle_clarify(user_input, selected_model)
                elif intent == "versions":
                    response = self._handle_versions(user_input, selected_model)
                elif intent == "market":
                    response = self._handle_market(user_input, selected_model)
                else: # rules
                    response = self._handle_rules(user_input, selected_model)
                
                self.active_context["intent"] = intent

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
        system_msg = """You are the MTG Know-it-all Judge. 
Explain that you are the ultimate authority on Magic: The Gathering. 
List your capabilities with examples:
- Rules & Interactions (e.g., 'How does Blood Moon interact with Urza's Saga?')
- Card Data & Editions (e.g., 'Show me all versions of Black Lotus')
- Market Intelligence (e.g., 'What are the daily movers?')
- Pricing (e.g., 'What is the price of Ragavan?')
Maintain your 'Know-it-all' persona: confident, expert, and slightly showy about your vast knowledge."""
        messages = [{"role": "system", "content": system_msg}]
        return self.llm.get_completion(model, messages + [{"role": "user", "content": query}])

    def _handle_off_topic(self, query, model):
        messages = [{"role": "system", "content": PROMPT_OFF_TOPIC}, {"role": "user", "content": query}]
        return self.llm.get_completion(model, messages)

    def _handle_clarify(self, query, model):
        messages = [{"role": "system", "content": PROMPT_CLARIFY}, {"role": "user", "content": query}]
        return self.llm.get_completion(model, messages)

    def _handle_versions(self, query, model):
        # 1. Update context with potential new cards
        self._refresh_card_context(query)
        
        if not self.active_context.get("cards"):
            return "No cards identified. Please specify a card name."

        # 2. Check for specific version selection (numeric input)
        version_choice = self._check_version_selection(query)

        # 3. Generate correct search query
        scryfall_query = self._generate_search_query(query, version_choice)
        print(f"🔍 Searching Scryfall: {scryfall_query}")

        versions = self.cards.get_card_versions(scryfall_query)
        if not versions:
            return f"No official records found for '{query}'."

        self.active_context["active_versions"] = versions

        # 4. Return detailed report or list menu
        if version_choice:
            return self._generate_version_report(version_choice)
        
        return self._generate_versions_menu(versions)

    def _generate_search_query(self, query, version_choice):
        """Generates the Scryfall search string based on context or user query."""
        if version_choice:
            return f"!\"{version_choice['name']}\""
        
        scryfall_query = self.llm.generate_search_query(query, self.history)
        
        # Fallback to context card name if query seems ambiguous
        card_names = self.active_context.get("cards", [])
        if card_names:
            if any(p in scryfall_query.lower() for p in ["this", "it", "that", "the card"]) or len(scryfall_query) < 3:
                scryfall_query = f"!\"{card_names[0]}\""
        
        return scryfall_query

    def _check_version_selection(self, query):
        """Checks if the user input corresponds to a previously listed version number."""
        if query.isdigit() and "active_versions" in self.active_context:
            try:
                idx = int(query) - 1
                versions = self.active_context["active_versions"]
                if 0 <= idx < len(versions):
                    choice = versions[idx]
                    print(f"📍 Selected Version: {choice['set_name']} ({choice['set']})")
                    return choice
            except ValueError:
                pass
        return None

    def _generate_version_report(self, version):
        """Generates a detailed pricing report for a specific card version."""
        cm_price = f"{version['prices'].get('eur', 'N/A')}€"
        ct_price = self.cardtrader.get_nm_price(version['id'])
        
        cm_link = get_cm_version_link(version['name'], version['set_name'])
        ct_link = get_ct_version_link(version['name'], version['set_name'])
        
        prices_to_compare = []
        if cm_price and "N/A" not in cm_price:
            try: prices_to_compare.append((float(cm_price.replace('€', '').strip()), "Cardmarket"))
            except ValueError: pass
        if ct_price and "N/A" not in ct_price:
            try: prices_to_compare.append((float(ct_price.replace('€', '').strip()), "Cardtrader"))
            except ValueError: pass
        
        lowest_display = min(prices_to_compare) if prices_to_compare else (None, None)
        lowest_str = f"{lowest_display[0]}€ ({lowest_display[1]})" if lowest_display[0] else "N/A"

        return (
            f"\n📊 {version['name']} | {version['set_name']}\n"
            f"{'-'*40}\n"
            f"💰 Lowest Price: {lowest_str}\n"
            f"\n🛒 [Buy on Cardmarket]({cm_link})\n"
            f"🛒 [Buy on Cardtrader]({ct_link})\n"
            f"{'-'*40}\n"
        )

    def _generate_versions_menu(self, versions):
        """Generates a list menu of available versions."""
        all_prices = []
        
        # Quick price sample
        for vx in versions:
            if vx['prices'].get('eur') and vx['prices']['eur'] != 'N/A':
                all_prices.append((float(vx['prices']['eur']), "Cardmarket"))
        
        # Check first 3 Cardtrader prices
        for vx in versions[:3]:
            ct_p = self.cardtrader.get_nm_price(vx['id'])
            if ct_p and ct_p != "N/A" and "€" in ct_p:
                try:
                    p_val = float(ct_p.replace('€', '').strip())
                    all_prices.append((p_val, "Cardtrader"))
                except ValueError: pass

        if all_prices:
            lowest_val, lowest_src = min(all_prices)
            price_summary = f"📉 Lowest found: {lowest_val}€ on {lowest_src}."
        else:
            price_summary = "📉 Pricing data currently unavailable for these versions."
        
        card_name = versions[0]['name'] if versions else "card"
        cm_search = get_cm_search_link(card_name)
        ct_search = get_ct_search_link(card_name)
        
        header = f"Found {len(versions)} versions of {card_name}.\n{price_summary}\n\n"
        header += f"🛒 STORE SEARCH:\n  • [Cardmarket]({cm_search})\n  • [Cardtrader]({ct_search})\n\n"
        header += "Which version would you like the full price analysis for?\n"
        
        menu = ""
        for i, v in enumerate(versions, 1):
            menu += f"{i}. {v['set_name']} ({v['set'].upper()}) - {v['rarity'].title()}\n"
            
        return header + menu + "\n(Reply with the number to see EN/NM minimums and 30-day trends.)"

    def _handle_market(self, query, model):
        from backend.app.core.config import PROMPT_MARKET_ANALYST
        print("📊 Analyzing market trends...")
        
        self._refresh_card_context(query)
        card_names = self.active_context.get("cards", [])

        extra_context = ""
        if card_names:
            card_name = card_names[0]
            print(f"🃏 Using Context for Market Analysis: {card_name}")
            
            scryfall_query = f"!\"{card_name}\""
            versions = self.cards.get_card_versions(scryfall_query)
            stats = self.market.get_card_stats(card_name, versions)
            
            if stats:
                extra_context = (
                    f"\nSPECIFIC CARD ANALYSIS ({stats['source']}): {card_name}\n"
                    f"- Avg Price: {stats['avg_price']}€\n"
                    f"- Price Spread: {stats['price_spread']}€ | Range: {stats['min_price']}€ - {stats['max_price']}€\n"
                    f"- Unique Versions: {stats['version_count']}\n"
                )
            else:
                extra_context = f"\nSPECIFIC CARD ANALYSIS: No consistent price data found for {card_name}.\n"

        messages = [
            {"role": "system", "content": PROMPT_MARKET_ANALYST},
            {"role": "user", "content": f"Query: {query}\n\n{extra_context}"}
        ]
        return self.llm.get_completion(model, messages, max_tokens=1000)

    def _handle_rules(self, query, model):
        """Processes complex rules and interactions with Critic/70B escalation."""
        # 1. Update Context
        self._refresh_card_context(query)
        card_names = self.active_context.get("cards", [])
        
        card_context = self._get_card_context(card_names)
        rules_context = self._get_rules_context(query)
        
        force_truth = "\n\nCRITICAL: EXTREME PRIORITY GIVEN TO 'CARD DATA (Source of Truth)'. USE ONLY PROVIDED TEXT."
        system_instruction = f"{PROMPT_JUDGE}\n\n{card_context}\n\n{rules_context}{force_truth}"
        
        messages = [{"role": "system", "content": system_instruction}]
        for i in range(0, len(self.history), 2):
            messages.append({"role": "user", "content": self.history[i]})
            messages.append({"role": "assistant", "content": self.history[i+1]})
        messages.append({"role": "user", "content": query})

        return self._get_completion_with_escalation(query, model, messages)

    def _refresh_card_context(self, query):
        """Extracts and updates card context from the query."""
        new_card_names = self.llm.extract_cards(query, self.history)
        if new_card_names:
            if new_card_names != self.active_context.get("cards"):
                print(f"🃏 Identified: {', '.join(new_card_names)}")
                self.active_context["cards"] = new_card_names
                self.active_context["selected_version"] = None 
        elif self.active_context.get("cards"):
             print(f"🃏 Using Context: {', '.join(self.active_context['cards'])}")

    def _get_card_context(self, card_names):
        """Fetches and formats Scryfall data for grounded rules analysis."""
        if not card_names:
            return ""
            
        scryfall_data = self.cards.get_card_data(card_names)
        if not scryfall_data:
            print(f"🚨 ALERT: Cards {card_names} found in query but Scryfall returned NO DATA.")
            return ""

        context = "CARD DATA (Source of Truth):\n"
        for card in scryfall_data:
            stats = ""
            if card.get('power') and card.get('toughness'):
                stats = f" | P/T: {card['power']}/{card['toughness']}"
            elif card.get('loyalty'):
                stats = f" | Loyalty: {card['loyalty']}"

            context += (
                f"Name: {card['name']}\n"
                f"Cost: {card['mana_cost']} | Type: {card['type_line']}{stats}\n"
                f"Oracle: {card['oracle_text']}\n"
            )
            if card.get('rulings'):
                rulings = card['rulings'][:8]
                context += "Official Rulings (Truncated):\n" + "\n".join([f"- {r}" for r in rulings]) + "\n"
            context += "-------------------\n"

        return context[:10000] + ("... [Truncated]" if len(context) > 10000 else "")

    def _get_rules_context(self, query):
        """Retrieves and truncates relevant rules from the vector index."""
        chunks = self.rag.retrieve(query, self.history)
        print(f"📚 {len(chunks)} rule chapters retrieved.")
        
        rules_text_list = []
        current_len = 0
        for c in chunks:
            chunk_str = f"[{c['rule_num']}] {c['text']}\n"
            if current_len + len(chunk_str) > 12000:
                rules_text_list.append("... [Additional rules truncated]")
                break
            rules_text_list.append(chunk_str)
            current_len += len(chunk_str)
            
        return "COMPREHENSIVE RULES:\n" + "".join(rules_text_list)

    def _get_completion_with_escalation(self, query, model, messages):
        """Handles LLM generation with automatic 8B -> 70B escalation if format fails."""
        from backend.app.utils.io import log_interaction
        
        result = self.llm.get_completion(model, messages)
        is_gold = (model == SMART_MODEL)
        
        if model == NORMAL_MODEL:
            is_valid, _ = self.llm.validate_format(result)
            if not is_valid and "rate_limit_exceeded" not in result:
                print("🕵️ Critic: Format invalid. Escalating to Deep (70B) model...")
                result = self.llm.get_completion(SMART_MODEL, messages)
                is_gold = True
        
        log_interaction(query, result, model, is_gold=is_gold)

        if "rate_limit_exceeded" in result or "Request too large" in result:
             return "I apologize, but that query generated too much technical data for my current memory speed. Please try a simpler question, or select [2] Deep (70B) for more complex interactions."
            
        return result

