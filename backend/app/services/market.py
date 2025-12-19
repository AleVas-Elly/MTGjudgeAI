import requests
from bs4 import BeautifulSoup
import numpy as np

class MarketIntelligenceService:
    def __init__(self, cardtrader_service):
        self.ct_service = cardtrader_service

    def get_market_movers(self):
        """
        Market movers functionality disabled as per user request to remove MTGStocks.
        Returns empty list for compatibility.
        """
        return []

    def analyze_arbitrage(self, card_name, cm_price_str, scryfall_id):
        """Calculates arbitrage opportunity between CM and CT."""
        try:
            if cm_price_str == "N/A" or not cm_price_str:
                return None
            cm_val = float(cm_price_str.replace('€', '').strip())
            
            ct_price_str = self.ct_service.get_nm_price(scryfall_id)
            if "N/A" in ct_price_str or not ct_price_str:
                return None
            
            try:
                ct_val = float(ct_price_str.replace('€', '').strip())
            except ValueError:
                return None
            
            diff = ct_val - cm_val
            pct_diff = (diff / cm_val) * 100 if cm_val > 0 else 0
            
            return {
                "cm": cm_val,
                "ct": ct_val,
                "diff": diff,
                "pct": pct_diff,
                "rating": "High" if abs(pct_diff) > 15 else "Normal"
            }
        except Exception:
            return None

    def get_card_stats(self, card_name, versions):
        """Generates statistical metadata for a card based on versions and prices."""
        if not versions:
            return {}
            
        prices = [float(v['prices']['eur']) for v in versions if v['prices']['eur'] not in ['N/A', None]]
        if not prices:
            return {}
            
        avg = round(sum(prices) / len(prices), 2)
        
        # Simple stats derived from Scryfall data only
        avg_30d = "N/A" # No historical data without external index
        trend_data = [] # No trend data without external index
        source = "Scryfall Current Data"

        sparkline = self.generate_sparkline(trend_data)

        # Simplified stats object
        return {
            "avg_price": avg,
            "max_price": max(prices),
            "min_price": min(prices),
            "price_spread": round(max(prices) - min(prices), 2),
            "version_count": len(versions),
            "source": source,
            "trend_graph": sparkline,
            "last_30d_avg": avg_30d
        }

    def generate_sparkline(self, data, length=10):
        """Generates a text-based sparkline for trends with start/end prices."""
        if not data: return ""
        chars = " ▂▃▄▅▆▇█"
        min_v, max_v = min(data), max(data)
        
        start_p = f"{data[0]}€"
        end_p = f"{data[-1]}€"
        
        if max_v == min_v: 
            return f"[{start_p} {chars[0] * len(data)} {end_p}]"
        
        res = ""
        for v in data:
            idx = int((v - min_v) / (max_v - min_v) * (len(chars) - 1))
            res += chars[idx]
        return f"[{start_p} {res} {end_p}]"

