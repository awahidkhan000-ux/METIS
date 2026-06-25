import requests

# Test Yahoo Finance for metal prices
metals = {
    "Copper": "HG=F",
    "Aluminum": "ALI=F", 
    "Nickel": "NI=F",
    "Iron Ore": "TIO=F"
}

for name, ticker in metals.items():
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        print(f"{name}: {r.status_code}")
    except Exception as e:
        print(f"{name}: FAILED — {e}")