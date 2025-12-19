import requests
import json

resp = requests.get("https://api.scryfall.com/cards/named", params={"exact": "The One Ring"})
print(json.dumps(resp.json(), indent=2))
