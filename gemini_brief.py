from dotenv import load_dotenv
load_dotenv()
import requests
import xml.etree.ElementTree as ET
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

METALS = {
    "Copper": {
        "ticker": "HG=F",
        "unit": "USD/lb",
        "routes": [
            {"name": "Chile → China", "chokepoints": ["Panama Canal", "South China Sea", "Taiwan Strait"], "risk_factors": ["mine strikes", "port congestion Valparaiso", "Panama Canal water levels"]},
            {"name": "Peru → China", "chokepoints": ["Panama Canal", "South China Sea"], "risk_factors": ["community blockades", "port congestion Callao"]},
            {"name": "DRC → Europe", "chokepoints": ["Cape of Good Hope", "Strait of Gibraltar"], "risk_factors": ["regional conflict DRC", "rail disruption to Dar es Salaam"]}
        ],
        "currency_pair": ("USD", "CNY"),
        "news_query": "copper supply chain disruption mining Chile Peru"
    },
    "Iron Ore": {
        "ticker": "TIO=F",
        "unit": "USD/t",
        "routes": [
            {"name": "Australia → China", "chokepoints": ["Lombok Strait", "South China Sea"], "risk_factors": ["Port Hedland congestion", "cyclone season"]},
            {"name": "Brazil → China", "chokepoints": ["Cape of Good Hope", "Strait of Malacca", "South China Sea"], "risk_factors": ["Vale port disruptions", "Malacca congestion"]},
            {"name": "South Africa → China", "chokepoints": ["Cape of Good Hope", "Strait of Malacca"], "risk_factors": ["Saldanha Bay port capacity", "Cape weather"]}
        ],
        "currency_pair": ("AUD", "CNY"),
        "news_query": "iron ore supply chain shipping disruption Australia China"
    },
    "Aluminum": {
        "ticker": "ALI=F",
        "unit": "USD/mt",
        "routes": [
            {"name": "Australia → Japan", "chokepoints": ["Lombok Strait", "South China Sea", "Philippine Sea"], "risk_factors": ["South China Sea tensions", "Pacific typhoon season"]},
            {"name": "Guinea → Europe", "chokepoints": ["Strait of Gibraltar", "Atlantic Ocean"], "risk_factors": ["Guinea port congestion", "political instability Guinea"]},
            {"name": "Middle East → Global", "chokepoints": ["Strait of Hormuz", "Bab el-Mandeb", "Suez Canal"], "risk_factors": ["Hormuz closure risk", "Iran conflict", "Red Sea security"]}
        ],
        "currency_pair": ("USD", "EUR"),
        "news_query": "aluminum supply chain disruption Middle East smelter"
    },
    "Nickel": {
        "ticker": "^SPGSIK",
        "unit": "USD/mt",
        "routes": [
            {"name": "Indonesia → China", "chokepoints": ["Makassar Strait", "South China Sea"], "risk_factors": ["Indonesian mining quota cuts", "export policy changes"]},
            {"name": "Philippines → China", "chokepoints": ["South China Sea"], "risk_factors": ["territorial tensions", "typhoon season"]},
            {"name": "Russia → Europe", "chokepoints": ["Baltic Sea", "Turkish Straits"], "risk_factors": ["sanctions on Russian metals", "Bosporus restrictions"]}
        ],
        "currency_pair": ("USD", "IDR"),
        "news_query": "nickel supply chain disruption Indonesia mining"
    }
}


def fetch_price(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        data = r.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return round(float(price), 4)
    except:
        return None


def fetch_fx(base, target):
    try:
        r = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=10)
        rate = r.json()["rates"].get(target)
        return round(rate, 4) if rate else None
    except:
        return None


def fetch_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en"
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        headlines = []
        for item in root.findall(".//item")[:4]:
            title = item.find("title")
            if title is not None and title.text:
                headlines.append(f"- {title.text}")
        return "\n".join(headlines) if headlines else "No headlines found."
    except:
        return "News unavailable."


def generate_brief(metal_name, route, price, fx_rate, news, base, target):
    price_text = f"{price}" if price else "unavailable"
    fx_text = f"{base}/{target}: {fx_rate}" if fx_rate else "unavailable"

    prompt = f"""You are a metals supply chain analyst. Write a brief for ONE trade route.

METAL: {metal_name}
ROUTE: {route['name']}
CHOKEPOINTS: {', '.join(route['chokepoints'])}
RISK FACTORS: {', '.join(route['risk_factors'])}
PRICE: {price_text}
FX: {fx_text}
NEWS: {news}

RULES:
- Only mention chokepoints listed above. Never invent others.
- Be short and specific.

Respond in EXACTLY this format, nothing else:

RISK: [HIGH / MEDIUM / LOW]
CONFIDENCE: [HIGH / MODERATE / LOW]
RISKS:
- [risk 1]
- [risk 2]
WATCH: [one thing to monitor]
ACTION: [one specific action]"""

    for attempt in range(3):
        try:
            r = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json={
                    "model": "openrouter/free",
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=25
            )
            result = r.json()
            if "choices" in result:
                content = result["choices"][0]["message"]["content"]
                if content and content.strip():
                    return content.strip()
            time.sleep(3)
        except:
            time.sleep(3)

    return "Brief unavailable — retry."


def process_metal(metal_name, config):
    price = fetch_price(config["ticker"])
    base, target = config["currency_pair"]
    fx_rate = fetch_fx(base, target)
    news = fetch_news(config["news_query"])

    results = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(generate_brief, metal_name, route, price, fx_rate, news, base, target): route["name"]
            for route in config["routes"]
        }
        for f in as_completed(futures):
            results[futures[f]] = f.result()

    return price, fx_rate, results