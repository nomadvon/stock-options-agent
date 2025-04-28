import logging
import time
import pandas as pd
from datetime import datetime, timedelta
import requests

from config.config import ALPACA_API_KEY, ALPACA_API_SECRET

logger = logging.getLogger(__name__)

class AlpacaConnector:
    """Connector for Alpaca API to fetch underlying stock price data"""
    
    BASE_URL = "https://data.alpaca.markets/v2"
    
    def __init__(self, api_key=ALPACA_API_KEY, api_secret=ALPACA_API_SECRET):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        })
    
    def _make_request(self, endpoint, params=None):
        """Make a request to Alpaca API with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"{self.BASE_URL}{endpoint}"
                response = self.session.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All retry attempts failed for endpoint {endpoint}")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def get_bars(self, symbol, timeframe='1D', start=None, end=None, limit=100):
        """Get historical price bars for a symbol"""
        if not start:
            start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
        if not end:
            end = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            
        params = {
            'start': start,
            'end': end,
            'limit': limit
        }
        
        endpoint = f"/stocks/{symbol}/bars"
        # Add timeframe parameter to the URL
        if timeframe:
            endpoint = f"{endpoint}?timeframe={timeframe}"
            
        try:
            response = self._make_request(endpoint, params)
            
            if 'bars' in response:
                df = pd.DataFrame(response['bars'])
                df['timestamp'] = pd.to_datetime(df['t'])
                df = df.rename(columns={
                    'o': 'open',
                    'h': 'high',
                    'l': 'low',
                    'c': 'close',
                    'v': 'volume',
                    't': 'timestamp'
                })
                return df
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_latest_quote(self, symbol):
        """Get the latest quote for a symbol"""
        endpoint = f"/stocks/{symbol}/quotes/latest"
        
        try:
            response = self._make_request(endpoint)
            if 'quote' in response:
                return response['quote']
            return None
            
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    def get_latest_trade(self, symbol):
        """Get the latest trade for a symbol"""
        endpoint = f"/stocks/{symbol}/trades/latest"
        
        try:
            response = self._make_request(endpoint)
            if 'trade' in response:
                return response['trade']
            return None
            
        except Exception as e:
            logger.error(f"Error getting trade for {symbol}: {e}")
            return None
