import requests
import os
import sys
from src.config import RULES_DOWNLOAD_URL, RULEBOOK_PATH
from src.utils.io import ensure_data_dir
from src.indexer import create_index
from src.br_updater import BRParser

def download_rules():
    """Downloads the official MTG Comprehensive Rules in TXT format."""
    print(f"📡 Downloading rules from: {RULES_DOWNLOAD_URL}")
    try:
        response = requests.get(RULES_DOWNLOAD_URL, timeout=30)
        response.raise_for_status()
        
        with open(RULEBOOK_PATH, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Rules saved to {RULEBOOK_PATH}")
        return True
    except Exception as e:
        print(f"❌ Failed to download rules: {e}")
        return False

def run_setup():
    """Performs the full data preparation sequence."""
    print("🚀 Starting automated data setup...")
    
    ensure_data_dir()
    
    # 1. Download Rulebook
    if not download_rules():
        print("🛑 Setup aborted: Rules download failed.")
        sys.exit(1)
    
    # 2. Run Indexer
    print("\n🧠 Initialising rulebook index...")
    create_index()
    
    # 3. Sync B&R List
    print("\n📋 Syncing Banned & Restricted list...")
    parser = BRParser()
    if parser.run():
        print("✅ B&R data updated.")
    else:
        print("⚠️  B&R sync failed, but setup will continue.")

    print("\n✨ Data setup complete! You can now run the main application.")

if __name__ == "__main__":
    run_setup()
