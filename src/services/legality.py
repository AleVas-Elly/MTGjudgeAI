import json
import os
from src.config import BR_FILE

class LegalityService:
    def __init__(self):
        self.br_data = self._load_data()

    def _load_data(self):
        """Loads cached B&R data."""
        if os.path.exists(BR_FILE):
            try:
                with open(BR_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def check_legality(self, card_name):
        """Cross-references card name with official B&R data."""
        status = []
        for fmt, list_data in self.br_data.items():
            if fmt == "Categorical":
                continue
            if isinstance(list_data, list):
                if card_name in list_data:
                    status.append(f"**BANNED** in {fmt}")
            elif isinstance(list_data, dict):
                if card_name in list_data.get("banned", []):
                    status.append(f"**BANNED** in {fmt}")
                if card_name in list_data.get("restricted", []):
                    status.append(f"**RESTRICTED** in {fmt}")
        return status
