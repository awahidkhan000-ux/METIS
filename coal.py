import requests

API_KEY = "AIzaSyBuy6Zc0t03Nkflm2ep1BsYZSpwj1k3RpQ"

coal_data = {
    "price": 135.40,
    "origin": "Australia",
    "destination": "Japan",
    "freight": 18.50,
    "currency": "AUD/JPY at 98.2"
}

prompt = f"""
You are a coal supply chain analyst.
Here is this week's market data:
- Coal price: {coal_data['price']} USD per ton
- Route: {coal_data['origin']} to {coal_data['destination']}
- Freight rate: {coal_data['freight']} USD per ton
- Currency: {coal_data['currency']}

Write a 150-word risk brief for a small commodity trader.
End with one specific recommendation.
"""

response = requests.post(
    url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent",
    params={"key": API_KEY},
    json={"contents": [{"parts": [{"text": prompt}]}]}
)

result = response.json()
print(result["candidates"][0]["content"]["parts"][0]["text"])             