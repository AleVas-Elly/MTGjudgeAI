from backend.app.core.config import SMART_MODEL, NORMAL_MODEL, PROMPT_OFF_TOPIC, PROMPT_CLARIFY, PROMPT_HISTORIAN, PROMPT_JUDGE, PROMPT_LOOKUP
from backend.app.utils.market_links import get_cm_search_link, get_cm_version_link, get_ct_search_link, get_ct_version_link
from backend.app.services.market import MarketIntelligenceService
from backend.app.services.rag import RAGService
from backend.app.services.llm import LLMService
# We need to import the services that this controller will manage

class ChatController:
    def __init__(self, llm_service, rag_service, card_service, legality_service, cardtrader_service, market_service):
        self.llm = llm_service
        self.rag = rag_service
        self.cards = card_service
        self.legality = legality_service
        self.cardtrader = cardtrader_service
        self.market = market_service
        # State is now passed per request, but we can maintain session context if we were using a DB.
        # For this refactor, we assume context is passed in or managed by the client/API session.
        self.active_context = {"cards": [], "intent": None, "active_versions": []}

    def process_message(self, user_input, history, smart_mode=False, context=None):
        """
        Main entry point for processing a user message.
        """
        if context:
            self.active_context = context

        selected_model = SMART_MODEL if smart_mode else NORMAL_MODEL
        
        # 1. Intent Classification
        intent = self.llm.classify_intent(user_input, history)
        
        # 1b. Handle Retry
        if intent == "retry":
            print(f"🔄 Retry detected. History length: {len(history)}")
            if len(history) >= 2:
                # Retrieve last user message (history is [User, Bot, User, Bot...])
                # We want the message at index -2 (the user's last query)
                last_user_query = history[-2]
                print(f"🔄 Retrying previous query: {last_user_query}")
                
                # Update inputs to emulate the old query
                user_input = last_user_query
                # We conceptually rewind history to before the failed exchange
                history = history[:-2]
                
                # Re-classify intent for the original query
                intent = self.llm.classify_intent(user_input, history)
            else:
                 return {
                    "response": "I cannot try again because there is no previous conversation history to retry.",
                    "intent": "meta",
                    "context": self.active_context
                }
        
        response = ""
        if intent == "meta":
            response = self._handle_meta(user_input, selected_model)
        elif intent == "off_topic":
            response = self._handle_off_topic(user_input, selected_model)
        elif intent == "clarify":
            response = self._handle_clarify(user_input, selected_model)
        elif intent == "lookup":
            response = self._handle_lookup(user_input, history, selected_model)
        elif intent == "versions":
            response = self._handle_versions(user_input, history, selected_model)
        elif intent == "market":
            response = self._handle_market(user_input, history, selected_model)
        else: # rules
            response = self._handle_rules(user_input, history, selected_model)
            
        self.active_context["intent"] = intent
        
        return {
            "response": response,
            "intent": intent,
            "context": self.active_context
        }

    def _handle_meta(self, query, model):
        system_msg = "You are the MTG Know-it-all Judge. Explain your authority on Magic: The Gathering."
        messages = [{"role": "system", "content": system_msg}]
        return self.llm.get_completion(model, messages + [{"role": "user", "content": query}])

    def _handle_off_topic(self, query, model):
        messages = [{"role": "system", "content": PROMPT_OFF_TOPIC}, {"role": "user", "content": query}]
        return self.llm.get_completion(model, messages)

    def _handle_clarify(self, query, model):
        messages = [{"role": "system", "content": PROMPT_CLARIFY}, {"role": "user", "content": query}]
        return self.llm.get_completion(model, messages)
        
    def _handle_lookup(self, query, history, model):
        card_names = self.llm.extract_cards(query, history)
        self._update_card_context(card_names)
        
        # Pre-fetch image markdown if context exists
        img_md = ""
        if self.active_context["cards"]:
            img_md = self._get_image_markdown(self.active_context["cards"])

        card_context = self._get_card_context(self.active_context["cards"])
        # No RAG context needed for simple lookup usually, but we can verify oracle text
        # Just send card context and request simple explanation
        
        system_instruction = f"{PROMPT_LOOKUP}\n\n{card_context}"
        messages = [{"role": "system", "content": system_instruction}, {"role": "user", "content": query}]
        
        response = self.llm.get_completion(model, messages)
        return img_md + response # Image FIRST

    def _handle_versions(self, query, history, model):
        # 1. New card or context?
        card_names = self.llm.extract_cards(query, history)
        self._update_card_context(card_names)
        
        if self.active_context.get("cards"):
            card_names = self.active_context["cards"]
        else:
            return "No cards identified. Please specify a card name."

        # 2. Check for version selection (numeric input)
        version_choice = None
        if query.isdigit() and "active_versions" in self.active_context:
            try:
                idx = int(query) - 1
                if 0 <= idx < len(self.active_context["active_versions"]):
                    version_choice = self.active_context["active_versions"][idx]
            except Exception: pass

        # 3. Generate query
        if version_choice:
            scryfall_query = f"!\"{version_choice['name']}\""
        else:
            scryfall_query = self.llm.generate_search_query(query, history)
        
        if card_names and not version_choice:
            # Fallback Heuristics:
            # 1. If generated query contains pronouns (it/that)
            # 2. If generated query is too short
            # 3. If generated query is simply the user input (LLM failure)
            # 4. If generated query has spaces but no '!' or quotes (likely bad generation)
            is_raw_input = scryfall_query.strip().lower() == query.strip().lower()
            looks_invalid = " " in scryfall_query and "!" not in scryfall_query and ":" not in scryfall_query
            has_pronouns = any(p in scryfall_query.lower() for p in ["this", "it", "that", "the card"])
            
            if has_pronouns or len(scryfall_query) < 3 or is_raw_input or looks_invalid:
                scryfall_query = f"!\"{card_names[0]}\""
            
        versions = self.cards.get_card_versions(scryfall_query)
        if not versions:
            return f"No official records found for '{query}'."

        self.active_context["active_versions"] = versions

        # 4. If a specific version was chosen, give the REPORT
        if version_choice:
            return self._generate_version_report(version_choice)

        # 5. Otherwise, give the INITIAL LIST
        return self._generate_versions_menu(versions, card_names)

    def _generate_version_report(self, v):
        # stocks = self.market.mtgstocks.get_card_trend(...) - REMOVED
        
        # Simplified Version Report using only current data
        cm_price = f"{v['prices'].get('eur', 'N/A')}€"
        ct_price = self.cardtrader.get_nm_price(v['id'])
        
        cm_link = get_cm_version_link(v['name'], v['set_name'])
        ct_link = get_ct_version_link(v['name'], v['set_name'])
        
        # Identify absolute lowest price
        prices_to_compare = []
        if cm_price and "N/A" not in cm_price:
             try: prices_to_compare.append((float(cm_price.replace('€', '').strip()), "Cardmarket"))
             except ValueError: pass
        if ct_price and "N/A" not in ct_price:
             try: prices_to_compare.append((float(ct_price.replace('€', '').strip()), "Cardtrader"))
             except ValueError: pass
        
        lowest_display = min(prices_to_compare) if prices_to_compare else (None, None)
        lowest_str = f"{lowest_display[0]}€ ({lowest_display[1]})" if lowest_display[0] else "N/A"

        report = (
            f"\n📊 {v['name']} | {v['set_name']}\n"
            f"{'-'*40}\n"
            f"💰 Lowest Price: {lowest_str}\n"
            f"\n🛒 [Buy on Cardmarket]({cm_link})\n"
            f"{'-'*40}\n"
        )
        return report

    def _generate_versions_menu(self, versions, card_names):
        all_prices = []
        for vx in versions:
            if vx['prices'].get('eur') and vx['prices']['eur'] != 'N/A':
                all_prices.append((float(vx['prices']['eur']), "Cardmarket"))
        
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
            price_summary = "📉 Pricing data checking..." 
        
        card_name = card_names[0] if card_names else "card"
        cm_search = get_cm_search_link(card_name)
        ct_search = get_ct_search_link(card_name)
        
        header = f"Found {len(versions)} versions of {card_name}.\n"
        header += f"{price_summary}\n\n"
        header += f"🛒 STORE SEARCH:\n"
        header += f"  • [Cardmarket]({cm_search})\n\n"
        header += "Which version would you like the full price analysis for?\n"
        
        menu = ""
        for i, v in enumerate(versions, 1):
             menu += f"{i}. {v['set_name']} ({v['set'].upper()}) - {v['rarity'].title()}\n"
        
        return header + menu

    def _handle_market(self, query, history, model):
        from backend.app.core.config import PROMPT_MARKET_ANALYST

        # Market Movers disabled
        movers_str = ""

        card_names = self.llm.extract_cards(query, history)
        if not card_names and self.active_context["cards"]:
            card_names = self.active_context["cards"]
        elif card_names:
            self.active_context["cards"] = card_names

        extra_context = ""
        if card_names:
             # Shortened logic for succinctness
             extra_context = f"Analyzing {card_names[0]}..."

        messages = [
            {"role": "system", "content": PROMPT_MARKET_ANALYST},
            {"role": "user", "content": f"Query: {query}\n\n{movers_str}\n{extra_context}"}
        ]
        response = self.llm.get_completion(model, messages, max_tokens=1000)
        
        # Append image if available
        if self.active_context["cards"]:
            response += self._get_image_markdown(self.active_context["cards"])
            
        return response


    def _update_card_context(self, new_card_names):
        if new_card_names:
            if new_card_names != self.active_context.get("cards"):
                self.active_context["cards"] = new_card_names
                self.active_context["active_versions"] = [] # Reset on switch

    def _get_card_context(self, card_names):
        if not card_names: return ""
        data = self.cards.get_card_data(card_names)
        if not data: return ""
        context = "CARD DATA:\n"
        for c in data:
            context += f"Name: {c['name']}\nOracle: {c['oracle_text']}\nType: {c['type_line']}\n---\n"
        return context

    def _get_image_markdown(self, card_names):
        """Fetches markdown image link for the first card in the list."""
        if not card_names: return ""
        data = self.cards.get_card_data([card_names[0]]) # Just get first card
        if data and data[0].get('image'):
             return f"\n\n![{data[0]['name']}]({data[0]['image']})"
        return ""

    def _handle_rules(self, query, history, model):
        card_names = self.llm.extract_cards(query, history)
        self._update_card_context(card_names)
        
        # Pre-fetch image markdown if context exists
        img_md = ""
        if self.active_context["cards"]:
            img_md = self._get_image_markdown(self.active_context["cards"])

        card_context = self._get_card_context(self.active_context["cards"])
        rules_context = self._get_rules_context(query, history)
        
        force_truth = "\n\nCRITICAL: EXTREME PRIORITY GIVEN TO 'CARD DATA'. USE ONLY PROVIDED TEXT."
        system_instruction = f"{PROMPT_JUDGE}\n\n{card_context}\n\n{rules_context}{force_truth}"
        
        messages = [{"role": "system", "content": system_instruction}]
        
        # Add history
        for i in range(0, len(history), 2):
            if i+1 < len(history):
                messages.append({"role": "user", "content": history[i]})
                messages.append({"role": "assistant", "content": history[i+1]})
        messages.append({"role": "user", "content": query})

        response = self.llm.get_completion(model, messages)
        # Append image to response
        return img_md + response

    def _get_rules_context(self, query, history):
         chunks = self.rag.retrieve(query, history)
         return "RULES:\n" + "\n".join([f"[{c['rule_num']}] {c['text']}" for c in chunks])
