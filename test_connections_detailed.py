import os
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

# Test Polygon.io with more details
polygon_key = os.getenv('POLYGON_API_KEY')
print(f"Testing Polygon API connection...")
print(f"Key (first 4 chars): {polygon_key[:4]}...")
polygon_url = f"https://api.polygon.io/v2/reference/news?limit=1&apiKey={polygon_key}"
try:
    polygon_response = requests.get(polygon_url)
    print(f"Polygon status: {polygon_response.status_code}")
    print(f"Full response: {polygon_response.text[:200]}")
    if not polygon_response.ok:
        print("This could indicate an issue with your API key or subscription level.")
except Exception as e:
    print(f"Error connecting to Polygon: {e}")

print("\n" + "-"*50 + "\n")

# Test Alpaca with more details
alpaca_key = os.getenv('ALPACA_API_KEY')
alpaca_secret = os.getenv('ALPACA_API_SECRET')
print(f"Testing Alpaca API connection...")
print(f"Key (first 4 chars): {alpaca_key[:4]}...")
print(f"Secret (first 4 chars): {alpaca_secret[:4]}...")
alpaca_url = "https://paper-api.alpaca.markets/v2/account"
alpaca_headers = {
    'APCA-API-KEY-ID': alpaca_key,
    'APCA-API-SECRET-KEY': alpaca_secret
}
try:
    alpaca_response = requests.get(alpaca_url, headers=alpaca_headers)
    print(f"Alpaca status: {alpaca_response.status_code}")
    print(f"Full response: {alpaca_response.text[:200]}")
    if not alpaca_response.ok:
        print("This suggests your API keys might be incorrect or your account might not be active.")
except Exception as e:
    print(f"Error connecting to Alpaca: {e}")
