import urllib.parse
import re

def slugify(text):
    """Generates a standard slug: lowercase, hyphens instead of spaces, omit special chars."""
    if not text: return ""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text

def get_cm_search_link(card_name):
    """Generates a Cardmarket search link for a card."""
    query = f"[{card_name}]"
    quoted = urllib.parse.quote(query)
    return f"https://www.cardmarket.com/en/Magic/Products/Search?searchMode=v2&idCategory=0&idExpansion=0&searchString={quoted}&exactMatch=on&idRarity=0&perSite=30"

def get_cm_version_link(card_name, set_name):
    """Generates a direct Cardmarket link for a specific version."""
    # CM Single URL format: https://www.cardmarket.com/en/Magic/Products/Singles/[Set]/[Card]
    # Slugification for CM is a bit different: spaces to hyphen, no dots/apostrophes
    cm_set = set_name.replace(" ", "-").replace("'", "").replace(".", "").replace(",", "")
    cm_card = card_name.replace(" ", "-").replace("'", "").replace(".", "").replace(",", "")
    return f"https://www.cardmarket.com/en/Magic/Products/Singles/{cm_set}/{cm_card}"

def get_ct_search_link(card_name):
    """Generates a Cardtrader search/versions link for a card."""
    slug = slugify(card_name)
    return f"https://www.cardtrader.com/en/cards/{slug}/versions"

def get_ct_version_link(card_name, set_name):
    """Generates a direct Cardtrader link for a specific version."""
    # CT Single URL format: https://www.cardtrader.com/en/cards/[card-slug]-[set-slug]
    card_slug = slugify(card_name)
    set_slug = slugify(set_name)
    return f"https://www.cardtrader.com/en/cards/{card_slug}-{set_slug}"
