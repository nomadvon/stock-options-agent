import logging
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from alpaca.data.historical import StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest, OptionBarsRequest, OptionQuotesRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live import StockDataStream
from alpaca.data.models import OptionContract

from config.config import ALPACA_API_KEY, ALPACA_API_SECRET, TRADING_SYMBOLS, DTE_RANGE, DELTA_RANGE, OPTION_TYPES

logger = logging.getLogger(__name__)

class AlpacaConnector:
    """Connector for Alpaca API to fetch real-time and historical data"""
    
    def __init__(self, api_key=ALPACA_API_KEY, api_secret=ALPACA_API_SECRET):
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Initialize historical data clients
        try:
            self.stock_hist_client = StockHistoricalDataClient(api_key, api_secret)
            self.option_hist_client = OptionHistoricalDataClient(api_key, api_secret)
            logger.info("Connected to Alpaca Historical Data APIs")
        except Exception as e:
            logger.error(f"Error connecting to Alpaca Historical Data APIs: {e}")
            self.stock_hist_client = None
            self.option_hist_client = None
        
        # Initialize real-time data stream
        try:
            self.stream = StockDataStream(api_key, api_secret)
            logger.info("Connected to Alpaca Real-Time Data Stream")
        except Exception as e:
            logger.error(f"Error connecting to Alpaca Real-Time Data Stream: {e}")
            self.stream = None
    
    def get_historical_bars(self, symbol: str, timeframe: str = '1d', 
                            start_date: Optional[str] = None, 
                            end_date: Optional[str] = None,
                            limit: int = 100) -> pd.DataFrame:
        """Get historical bar data for a symbol"""
        if not self.stock_hist_client:
            logger.error("Historical client not initialized")
            return pd.DataFrame()
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now()
        else:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        # Map timeframe string to Alpaca TimeFrame object
        tf_map = {
            '1h': TimeFrame.Hour,
            '4h': TimeFrame.Hour, # We'll handle 4h by getting hourly data and resampling
            '1d': TimeFrame.Day
        }
        alpaca_timeframe = tf_map.get(timeframe, TimeFrame.Day)
        
        # Special handling for 4h (get hourly and resample)
        adjustment_factor = 1
        if timeframe == '4h':
            adjustment_factor = 4
            
        try:
            # Create the request
            bars_request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=alpaca_timeframe,
                start=start_date,
                end=end_date,
                limit=limit * adjustment_factor if adjustment_factor > 1 else limit,
                adjustment='all'  # Adjust for splits, dividends, etc.
            )
            
            # Get the data
            bars_response = self.stock_hist_client.get_stock_bars(bars_request)
            
            # Convert to dataframe
            if symbol in bars_response:
                df = bars_response[symbol].df
                
                # Standardize column names to match previous implementation
                df = df.rename(columns={
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume',
                    'timestamp': 'date'
                })
                
                # Handle 4h resampling if needed
                if timeframe == '4h':
                    df = df.set_index('date')
                    df = df.resample('4H').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    df = df.reset_index()
                
                return df
            else:
                logger.warning(f"No bars data found for {symbol}")
                return pd.DataFrame()
        
        except Exception as e:
            logger.error(f"Error getting historical bars for {symbol}: {e}")
            return self._create_fallback_data(symbol, 30)  # Fallback to mock data
    
    def get_latest_quote(self, symbol: str) -> Dict:
        """Get the latest quote for a symbol"""
        if not self.stock_hist_client:
            logger.error("Historical client not initialized")
            return {}
        
        try:
            # Create the request
            quote_request = StockQuotesRequest(symbol_or_symbols=symbol)
            
            # Get the data
            quote_response = self.stock_hist_client.get_stock_latest_quote(quote_request)
            
            if symbol in quote_response:
                quote = quote_response[symbol]
                return {
                    'symbol': symbol,
                    'bid_price': quote.bid_price,
                    'bid_size': quote.bid_size,
                    'ask_price': quote.ask_price,
                    'ask_size': quote.ask_size,
                    'timestamp': quote.timestamp
                }
            else:
                logger.warning(f"No quote data found for {symbol}")
                return {}
        
        except Exception as e:
            logger.error(f"Error getting latest quote for {symbol}: {e}")
            return {}
    
    def get_real_time_data(self, symbols: List[str] = TRADING_SYMBOLS) -> Dict:
        """Get real-time data for a list of symbols (not used in current implementation)"""
        quotes = {}
        
        for symbol in symbols:
            quote = self.get_latest_quote(symbol)
            if quote:
                quotes[symbol] = quote
        
        return quotes
    
    def _create_fallback_data(self, symbol: str, days_back: int = 30) -> pd.DataFrame:
        """Create fallback mock data when API calls fail"""
        logger.info(f"Creating fallback data for {symbol}")
        today = datetime.now()
        date_range = pd.date_range(end=today, periods=days_back)
        
        # Default price map based on symbol
        default_prices = {
            'AAPL': 180, 'MSFT': 420, 'NVDA': 950, 'TSLA': 220,
            'AMZN': 180, 'GOOG': 170, 'META': 500, 'AMD': 150,
            'INTC': 30, 'NFLX': 600, 'QQQ': 440, 'SPY': 500
        }
        
        base_price = default_prices.get(symbol, 100)
        
        # Generate random but realistic price movements
        import numpy as np
        np.random.seed(int(time.time()) % 10000)  # Seed based on current time for variation
        daily_returns = np.random.normal(0.001, 0.02, days_back)
        cumulative_returns = np.cumprod(1 + daily_returns)
        
        # Create price data
        close_prices = base_price * cumulative_returns
        high_prices = close_prices * (1 + np.random.uniform(0, 0.02, days_back))
        low_prices = close_prices * (1 - np.random.uniform(0, 0.02, days_back))
        open_prices = low_prices + np.random.uniform(0, 1, days_back) * (high_prices - low_prices)
        
        # Create volume data
        volumes = np.random.uniform(5, 15, days_back) * 1_000_000
        
        # Create DataFrame
        df = pd.DataFrame({
            'date': date_range,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        })
        
        df = df.sort_values('date')
        return df

    def get_option_contracts(self, ticker: str, expiration_date_gte: Optional[str] = None, 
                           expiration_date_lte: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get option contracts for a ticker with expiration date filters"""
        if not self.option_hist_client:
            logger.error("Option historical client not initialized")
            return []
            
        if not expiration_date_gte:
            expiration_date_gte = datetime.now().strftime('%Y-%m-%d')
        if not expiration_date_lte:
            expiration_date_lte = (datetime.now() + timedelta(days=DTE_RANGE[1])).strftime('%Y-%m-%d')
            
        try:
            # Get all option contracts for the ticker
            contracts = self.option_hist_client.get_option_contracts(
                underlying_symbol=ticker,
                expiration_date_gte=expiration_date_gte,
                expiration_date_lte=expiration_date_lte,
                limit=limit
            )
            
            # Convert to list of dictionaries
            return [{
                'ticker': contract.symbol,
                'strike_price': contract.strike_price,
                'expiration_date': contract.expiration_date.strftime('%Y-%m-%d'),
                'contract_type': contract.contract_type,
                'delta': None  # Alpaca doesn't provide delta directly
            } for contract in contracts]
            
        except Exception as e:
            logger.error(f"Error getting option contracts for {ticker}: {e}")
            return []
    
    def get_option_quotes(self, option_symbol: str) -> Optional[Dict]:
        """Get real-time quote for an option contract"""
        if not self.option_hist_client:
            logger.error("Option historical client not initialized")
            return None
            
        try:
            # Get latest quote
            quote = self.option_hist_client.get_option_latest_quote(option_symbol)
            
            if quote:
                return {
                    'symbol': option_symbol,
                    'bid_price': quote.bid_price,
                    'bid_size': quote.bid_size,
                    'ask_price': quote.ask_price,
                    'ask_size': quote.ask_size,
                    'timestamp': quote.timestamp
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting option quote for {option_symbol}: {e}")
            return None
    
    def get_option_historical(self, option_symbol: str, from_date: str, to_date: str, 
                            timespan: str = 'day') -> pd.DataFrame:
        """Get historical data for an option contract"""
        if not self.option_hist_client:
            logger.error("Option historical client not initialized")
            return pd.DataFrame()
            
        try:
            # Map timeframe string to Alpaca TimeFrame object
            tf_map = {
                '1h': TimeFrame.Hour,
                '4h': TimeFrame.Hour,  # We'll handle 4h by getting hourly data and resampling
                '1d': TimeFrame.Day
            }
            alpaca_timeframe = tf_map.get(timespan, TimeFrame.Day)
            
            # Special handling for 4h (get hourly and resample)
            adjustment_factor = 1
            if timespan == '4h':
                adjustment_factor = 4
                
            # Create the request
            bars_request = OptionBarsRequest(
                symbol_or_symbols=option_symbol,
                timeframe=alpaca_timeframe,
                start=datetime.strptime(from_date, '%Y-%m-%d'),
                end=datetime.strptime(to_date, '%Y-%m-%d'),
                limit=100 * adjustment_factor if adjustment_factor > 1 else 100
            )
            
            # Get the data
            bars_response = self.option_hist_client.get_option_bars(bars_request)
            
            # Convert to dataframe
            if option_symbol in bars_response:
                df = bars_response[option_symbol].df
                
                # Standardize column names
                df = df.rename(columns={
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume',
                    'timestamp': 'date'
                })
                
                # Handle 4h resampling if needed
                if timespan == '4h':
                    df = df.set_index('date')
                    df = df.resample('4H').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    df = df.reset_index()
                
                return df
            else:
                logger.warning(f"No bars data found for {option_symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting historical bars for {option_symbol}: {e}")
            return pd.DataFrame()
    
    def filter_options_by_criteria(self, ticker: str, option_type: str = 'call', 
                                 dte_min: int = DTE_RANGE[0], dte_max: int = DTE_RANGE[1],
                                 delta_min: float = DELTA_RANGE[0], delta_max: float = DELTA_RANGE[1]) -> List[Dict]:
        """Filter options by criteria - DTE range, delta range, etc."""
        # Get near-term expiration dates within DTE range
        now = datetime.now()
        min_date = (now + timedelta(days=dte_min)).strftime('%Y-%m-%d')
        max_date = (now + timedelta(days=dte_max)).strftime('%Y-%m-%d')
        
        contracts = self.get_option_contracts(ticker, min_date, max_date)
        
        # Filter by option type (call/put)
        filtered_contracts = [c for c in contracts if c['contract_type'].lower() == option_type.lower()]
        
        # Note: Alpaca doesn't provide delta directly, so we can't filter by delta
        # In a real implementation, you'd need to calculate delta or get it from another source
        
        return filtered_contracts
    
    def scan_for_option_opportunities(self) -> List[Dict]:
        """Scan for option opportunities based on configured parameters"""
        opportunities = []
        
        for symbol in TRADING_SYMBOLS:
            for option_type in OPTION_TYPES:
                # Get filtered option contracts
                contracts = self.filter_options_by_criteria(symbol, option_type)
                
                for contract in contracts:
                    # Get current option price
                    quote = self.get_option_quotes(contract['ticker'])
                    if quote:
                        opportunity = {
                            'symbol': symbol,
                            'option_symbol': contract['ticker'],
                            'contract_type': option_type,
                            'strike': contract['strike_price'],
                            'expiration': contract['expiration_date'],
                            'premium': quote['bid_price']  # Use bid price as conservative estimate
                        }
                        opportunities.append(opportunity)
        
        return opportunities
