import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Test Polygon.io
polygon_key = os.getenv('POLYGON_API_KEY')
print(f"Testing Polygon API connection...")
polygon_url = f"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2023-01-01/2023-01-10?apiKey={polygon_key}"
polygon_response = requests.get(polygon_url)
print(f"Polygon status: {polygon_response.status_code}")
print(f"Response: {polygon_response.json()[:100] if polygon_response.ok else 'Failed'}\n")

# Test Alpaca
alpaca_key = os.getenv('ALPACA_API_KEY')
alpaca_secret = os.getenv('ALPACA_API_SECRET')
print(f"Testing Alpaca API connection...")
alpaca_url = "https://paper-api.alpaca.markets/v2/account"
alpaca_headers = {
    'APCA-API-KEY-ID': alpaca_key,
    'APCA-API-SECRET-KEY': alpaca_secret
}
alpaca_response = requests.get(alpaca_url, headers=alpaca_headers)
print(f"Alpaca status: {alpaca_response.status_code}")
print(f"Response: {alpaca_response.json() if alpaca_response.ok else 'Failed'}\n")

# Test NewsAPI
news_key = os.getenv('NEWS_API_KEY')
print(f"Testing NewsAPI connection...")
news_url = f"https://newsapi.org/v2/everything?q=AAPL&apiKey={news_key}&pageSize=1"
news_response = requests.get(news_url)
print(f"NewsAPI status: {news_response.status_code}")
print(f"Response: {news_response.json() if news_response.ok else 'Failed'}\n")

# Test Discord Webhook
discord_url = os.getenv('DISCORD_WEBHOOK_URL')
print(f"Testing Discord Webhook...")
discord_data = {"content": "Test message from Options Swing Trade Agent"}
discord_response = requests.post(discord_url, json=discord_data)
print(f"Discord Webhook status: {discord_response.status_code}")
print(f"{'Success' if discord_response.ok else 'Failed'}\n")
