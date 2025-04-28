import logging
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
from config.config import POLYGON_API_KEY, TRADING_SYMBOLS, OPTION_TYPES, DTE_RANGE, DELTA_RANGE

logger = logging.getLogger(__name__)

class PolygonConnector:
    """Connector for Polygon.io API to fetch real-time and historical options data"""
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key=POLYGON_API_KEY):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
    def _make_request(self, endpoint, params=None):
        """Make a request to Polygon API with retry logic"""
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
    
    def get_option_contracts(self, ticker, expiration_date_gte=None, expiration_date_lte=None, limit=100):
        """Get option contracts for a ticker with expiration date filters"""
        if not expiration_date_gte:
            expiration_date_gte = datetime.now().strftime('%Y-%m-%d')
        if not expiration_date_lte:
            expiration_date_lte = (datetime.now() + timedelta(days=DTE_RANGE[1])).strftime('%Y-%m-%d')
            
        params = {
            'underlying_ticker': ticker,
            'expiration_date.gte': expiration_date_gte,
            'expiration_date.lte': expiration_date_lte,
            'limit': limit
        }
        
        endpoint = "/v3/reference/options/contracts"
        response = self._make_request(endpoint, params)
        return response['results'] if 'results' in response else []
    
    def get_option_quotes(self, option_symbol):
        """Get real-time quote for an option contract"""
        endpoint = f"/v2/last/trade/{option_symbol}"
        response = self._make_request(endpoint)
        return response['results'] if 'results' in response else None
    
    def get_option_historical(self, option_symbol, from_date, to_date, timespan='day'):
        """Get historical data for an option contract"""
        params = {
            'from': from_date,
            'to': to_date,
            'timespan': timespan,
            'limit': 50000
        }
        
        endpoint = f"/v2/aggs/ticker/{option_symbol}/range/1/{timespan}/{from_date}/{to_date}"
        response = self._make_request(endpoint)
        
        if 'results' in response:
            df = pd.DataFrame(response['results'])
            df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
            return df
        return pd.DataFrame()
    
    def filter_options_by_criteria(self, ticker, option_type='call', dte_min=DTE_RANGE[0], dte_max=DTE_RANGE[1], 
                                delta_min=DELTA_RANGE[0], delta_max=DELTA_RANGE[1]):
        """Filter options by criteria - DTE range, delta range, etc."""
        # Get near-term expiration dates within DTE range
        now = datetime.now()
        min_date = (now + timedelta(days=dte_min)).strftime('%Y-%m-%d')
        max_date = (now + timedelta(days=dte_max)).strftime('%Y-%m-%d')
        
        contracts = self.get_option_contracts(ticker, min_date, max_date)
        
        # Filter by option type (call/put)
        filtered_contracts = [c for c in contracts if c['contract_type'].lower() == option_type]
        
        # For a real implementation, you'd need to get greeks from another API or calculate them
        # This is a placeholder for future implementation
        
        return filtered_contracts
    
    def get_real_time_data(self, symbols=TRADING_SYMBOLS):
        """Get real-time data for multiple symbols"""
        ticker_quotes = {}
        
        for symbol in symbols:
            endpoint = f"/v2/last/trade/{symbol}"
            response = self._make_request(endpoint)
            
            if 'results' in response:
                ticker_quotes[symbol] = response['results']
        
        return ticker_quotes
    
    def scan_for_option_opportunities(self):
        """Scan for option opportunities based on configured parameters"""
        opportunities = []
        
        for symbol in TRADING_SYMBOLS:
            for option_type in OPTION_TYPES:
                # Get filtered option contracts
                contracts = self.filter_options_by_criteria(symbol, option_type)
                
                for contract in contracts:
                    # In a real implementation, you'd evaluate the options here
                    # based on various criteria
                    
                    # Placeholder for now
                    opportunity = {
                        'symbol': symbol,
                        'option_symbol': contract['ticker'],
                        'contract_type': option_type,
                        'strike': contract['strike_price'],
                        'expiration': contract['expiration_date'],
                        'premium': None  # Will be filled with real data
                    }
                    
                    # Get current option price
                    quote = self.get_option_quotes(contract['ticker'])
                    if quote:
                        opportunity['premium'] = quote['p']  # price
                        opportunities.append(opportunity)
        
        return opportunities
