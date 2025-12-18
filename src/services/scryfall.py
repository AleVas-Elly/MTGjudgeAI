import requests
from src.config import SCRTYFALL_NAMED_URL, SCRTYFALL_SEARCH_URL

class CardService:
    @staticmethod
    def get_card_data(card_names):
        """Fetches Oracle text and metadata for a list of cards."""
        card_data = []
        for name in card_names:
            try:
                resp = requests.get(SCRTYFALL_NAMED_URL, params={"exact": name}, timeout=10)
                if resp.status_code != 200:
                    continue
                
                data = resp.json()
                info = {
                    "name": data.get("name"),
                    "mana_cost": data.get("mana_cost", "N/A"),
                    "type_line": data.get("type_line", "N/A"),
                    "oracle_text": data.get("oracle_text", "N/A"),
                    "power": data.get("power"),
                    "toughness": data.get("toughness"),
                    "loyalty": data.get("loyalty"),
                    "artist": data.get("artist"),
                    "set_name": data.get("set_name"),
                    "rarity": data.get("rarity"),
                    "rulings": []
                }
                
                rulings_url = data.get("rulings_uri")
                if rulings_url:
                    r_resp = requests.get(rulings_url, timeout=10)
                    if r_resp.status_code == 200:
                        r_data = r_resp.json()
                        info["rulings"] = [r.get("comment") for r in r_data.get("data", [])]
                
                card_data.append(info)
            except Exception:
                continue
        return card_data

    @staticmethod
    def get_card_versions(card_name):
        """Fetches all unique prints of a card."""
        versions = []
        params = {
            "q": f'!"{card_name}"',
            "unique": "prints",
            "order": "released",
            "dir": "asc"
        }
        
        try:
            resp = requests.get(SCRTYFALL_SEARCH_URL, params=params, timeout=10)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            for item in data.get("data", [])[:25]:
                prices = item.get("prices", {})
                legals = [f"{f}:{s}" for f, s in item.get("legalities", {}).items() if s != "not_legal"]
                
                versions.append({
                    "set_name": item.get("set_name"),
                    "set": item.get("set").upper(),
                    "released_at": item.get("released_at"),
                    "collector_number": item.get("collector_number"),
                    "rarity": item.get("rarity").capitalize(),
                    "artist": item.get("artist"),
                    "finishes": item.get("finishes", []),
                    "prices": {
                        "eur": prices.get("eur", "N/A"),
                        "eur_foil": prices.get("eur_foil", "N/A"),
                        "usd": prices.get("usd", "N/A"),
                        "usd_foil": prices.get("usd_foil", "N/A"),
                        "tix": prices.get("tix", "N/A")
                    },
                    "legalities": ", ".join(legals)
                })
        except Exception:
            pass
        return versions
