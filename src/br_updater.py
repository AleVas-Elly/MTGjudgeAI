import requests
from bs4 import BeautifulSoup
import json
import os
from src.config import BR_URL, BR_FILE

class BRParser:
    def __init__(self):
        self.url = BR_URL
        self.data = {}

    def run(self):
        """Fetches and parses the B&R list."""
        print(f"Syncing with: {self.url}")
        try:
            resp = requests.get(self.url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # The WotC page uses headers for formats and UL/LI for cards
            # We'll look for sections containing "Banned" or "Restricted"
            
            sections = soup.find_all(['h3', 'h4'])
            for section in sections:
                title = section.get_text().strip()
                if "Banned Cards" in title or "Banned and Restricted" in title:
                    format_name = title.split(" Banned")[0].strip()
                    cards = []
                    
                    # Look for the next siblings until another header
                    node = section.find_next_sibling()
                    while node and node.name not in ['h3', 'h4']:
                        if node.name == 'ul':
                            cards.extend([li.get_text().strip() for li in node.find_all('li')])
                        node = node.find_next_sibling()
                    
                    if cards:
                        if "Vintage" in format_name:
                            # Vintage often has split lists, we'll handle this in a simplified way
                            self.data["Vintage"] = {"banned": [c for c in cards if "banned" in title.lower()], 
                                                   "restricted": [c for c in cards if "restricted" in title.lower()]}
                        else:
                            self.data[format_name] = cards

            # Add categorical bans if sections found, or defaults
            self.data["Categorical"] = {
                "Attractions": "Banned in Standard, Modern, Legacy, Vintage, Pauper",
                "Stickers": "Banned in Standard, Modern, Legacy, Vintage, Pauper"
            }

            self._save()
            print(f"Successfully synced {len(self.data)} formats.")
            return True
        except Exception as e:
            print(f"Sync failed: {e}")
            return False

    def _save(self):
        os.makedirs(os.path.dirname(BR_FILE), exist_ok=True)
        with open(BR_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

if __name__ == "__main__":
    parser = BRParser()
    parser.run()
