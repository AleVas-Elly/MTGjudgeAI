import requests
import keyring
from backend.app.core.config import SERVICE_NAME

class CardTraderService:
    def __init__(self):
        self.api_key = keyring.get_password(SERVICE_NAME, "cardtrader_api_key")
        self.base_url = "https://api.cardtrader.com/api/v2"

    def get_nm_price(self, scryfall_id):
        """Fetches the English Near Mint price for a card using its Scryfall ID."""
        if not self.api_key:
            return "N/A (Key missing)"
        
        try:
            # 1. Get Blueprints for Scryfall ID
            headers = {"Authorization": f"Bearer {self.api_key}"}
            # Note: CardTrader API structure varies, this is a standard blueprints lookup
            resp = requests.get(
                f"{self.base_url}/blueprints/export?scryfall_id={scryfall_id}",
                headers=headers,
                timeout=10
            )
            if resp.status_code != 200:
                return "N/A"
            
            blueprints = resp.json()
            if not blueprints:
                return "N/A"
            
            # 2. Find the best English NM price (simplified)
            # This logic depends on the specific CT API response format
            # For now, we return a placeholder or link if we can't parse complex market depth
            return "Fetching..." # Placeholder for real integration
        except Exception:
            return "N/A"
