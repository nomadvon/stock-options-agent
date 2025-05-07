import logging
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import os
import pytz

from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live import StockDataStream
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest
from alpaca.trading.enums import AssetClass, OrderSide, TimeInForce

from config.config import ALPACA_API_KEY, ALPACA_API_SECRET, TRADING_SYMBOLS, DTE_RANGE, DELTA_RANGE, OPTION_TYPES

logger = logging.getLogger(__name__)

class AlpacaConnector:
    """Connector for Alpaca API to fetch real-time and historical data"""
    
    def __init__(self, api_key=ALPACA_API_KEY, api_secret=ALPACA_API_SECRET):
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Initialize clients
        try:
            self.stock_hist_client = StockHistoricalDataClient(api_key, api_secret)
            self.trading_client = TradingClient(api_key, api_secret, paper=True)  # Use paper trading
            logger.info("Connected to Alpaca APIs")
        except Exception as e:
            logger.error(f"Error connecting to Alpaca APIs: {e}")
            self.stock_hist_client = None
            self.trading_client = None
        
        # Initialize real-time data stream
        try:
            self.stream = StockDataStream(api_key, api_secret)
            logger.info("Connected to Alpaca Real-Time Data Stream")
        except Exception as e:
            logger.error(f"Error connecting to Alpaca Real-Time Data Stream: {e}")
            self.stream = None

    def is_market_open(self) -> bool:
        """
        Check if the market is currently open.
        
        Returns:
            bool: True if market is open, False otherwise
        """
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Error checking market status: {str(e)}")
            return False
            
    def get_market_hours(self) -> Dict[str, datetime]:
        """
        Get today's market hours.
        
        Returns:
            Dict with 'open' and 'close' times in UTC
        """
        try:
            clock = self.trading_client.get_clock()
            return {
                'open': clock.next_open,
                'close': clock.next_close
            }
        except Exception as e:
            logger.error(f"Error getting market hours: {str(e)}")
            return None

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get the current price for a symbol"""
        try:
            # Create the request
            quote_request = StockQuotesRequest(symbol_or_symbols=symbol)
            
            # Get the latest quote
            quote_response = self.stock_hist_client.get_stock_latest_quote(quote_request)
            
            if symbol in quote_response:
                quote = quote_response[symbol]
                if hasattr(quote, 'ask_price') and quote.ask_price:
                    return float(quote.ask_price)
            
            # Fallback to getting latest bar if quote is not available
            bars_request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=(datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),
                end=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            bars_response = self.stock_hist_client.get_stock_bars(bars_request)
            if symbol in bars_response:
                latest_bar = bars_response[symbol].df.iloc[-1]
                return float(latest_bar['close'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_options_chain(self, symbol: str, expiration_date: str, 
                         option_type: str) -> List[Dict]:
        """Get options chain for a symbol"""
        try:
            # Format expiration date for Alpaca
            exp_date = datetime.strptime(expiration_date, '%m-%d-%y')
            formatted_date = exp_date.strftime('%Y-%m-%d')
            
            # Since we don't have direct options data access, simulate it for testing
            # In production, you would use a proper options data provider
            current_price = self.get_current_price(symbol)
            if not current_price:
                return []
            
            # Create simulated options chain with strikes around current price
            strikes = [
                current_price * (1 + i * 0.01)  # Strikes at 1% intervals
                for i in range(-5, 6)  # 5 strikes above and below current price
            ]
            
            options_chain = []
            for strike in strikes:
                # Simulate option premium based on strike and current price
                # This is a more realistic model for testing
                distance_from_strike = abs(current_price - strike) / current_price  # As percentage
                time_to_expiry = (exp_date - datetime.now()).days / 365.0  # Years to expiry
                
                # Base time value (decays with time to expiry)
                time_value = 0.002 * (1 - time_to_expiry)  # 0.2% base, decaying with time
                
                # Intrinsic value (if any)
                intrinsic_value = max(0, 
                    (current_price - strike) / current_price if option_type == 'call' 
                    else (strike - current_price) / current_price
                ) * 0.5  # Scale down intrinsic value
                
                # Volatility component (higher for strikes closer to current price)
                volatility = max(0.0005, 0.002 * (1 - distance_from_strike))  # 0.05% to 0.2%
                
                # Calculate premium as percentage of stock price
                premium_pct = time_value + intrinsic_value + volatility
                premium = current_price * premium_pct * 0.1  # Scale down final premium
                
                # Only include options with premiums between $0.01 and $2.50
                if 0.01 <= premium <= 2.50:
                    options_chain.append({
                        'strike': float(strike),
                        'last_price': float(premium),
                        'volume': 1000,  # Simulated volume
                        'open_interest': 500  # Simulated open interest
                    })
            
            return options_chain
            
        except Exception as e:
            logger.error(f"Error getting options chain for {symbol}: {e}")
            return []
    
    def get_historical_bars(self, symbol: str, timeframe: str, 
                          from_date: str, to_date: str) -> pd.DataFrame:
        """Get historical price data"""
        try:
            # Convert timeframe to Alpaca TimeFrame
            tf = TimeFrame.Minute
            if timeframe == '1h':
                tf = TimeFrame.Hour
            elif timeframe == '4h':
                tf = TimeFrame.Hour
            elif timeframe == '1d':
                tf = TimeFrame.Day
            
            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=from_date,
                end=to_date
            )
            
            # Get bars
            bars = self.stock_hist_client.get_stock_bars(request)
            
            # Convert to DataFrame
            df = pd.DataFrame(bars.df)
            if not df.empty:
                df.reset_index(inplace=True)
                df.rename(columns={'timestamp': 'date'}, inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical bars for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_latest_quote(self, symbol: str) -> Dict:
        """Get the latest quote for a symbol"""
        try:
            # Create the request
            quote_request = StockQuotesRequest(symbol_or_symbols=symbol)
            
            # Get the latest quote
            quote_response = self.stock_hist_client.get_stock_latest_quote(quote_request)
            
            if symbol in quote_response:
                quote = quote_response[symbol]
                return {
                    'ask_price': float(quote.ask_price),
                    'ask_size': int(quote.ask_size),
                    'bid_price': float(quote.bid_price),
                    'bid_size': int(quote.bid_size),
                    'timestamp': quote.timestamp
                }
            
            # Fallback to getting latest bar if quote is not available
            bars_request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=(datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),
                end=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            bars_response = self.stock_hist_client.get_stock_bars(bars_request)
            if symbol in bars_response:
                latest_bar = bars_response[symbol].df.iloc[-1]
                return {
                    'ask_price': float(latest_bar['close']),
                    'ask_size': int(latest_bar['volume']),
                    'bid_price': float(latest_bar['close']),
                    'bid_size': int(latest_bar['volume']),
                    'timestamp': latest_bar.name
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest quote for {symbol}: {e}")
            return None
    
    def get_option_contracts(self, ticker: str, expiration_date_gte: Optional[str] = None, 
                           expiration_date_lte: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get option contracts for a ticker with expiration date filters"""
        if not self.trading_client:
            logger.error("Trading client not initialized")
            return []
            
        if not expiration_date_gte:
            expiration_date_gte = datetime.now().strftime('%Y-%m-%d')
        if not expiration_date_lte:
            expiration_date_lte = (datetime.now() + timedelta(days=DTE_RANGE[1])).strftime('%Y-%m-%d')
            
        try:
            # Get all option contracts for the ticker
            request = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
            options = self.trading_client.get_all_options(ticker)
            
            # Filter by expiration date
            start_date = datetime.strptime(expiration_date_gte, '%Y-%m-%d')
            end_date = datetime.strptime(expiration_date_lte, '%Y-%m-%d')
            
            filtered_options = [
                opt for opt in options 
                if start_date <= opt.expiration_date <= end_date
            ][:limit]
            
            # Convert to list of dictionaries
            return [{
                'ticker': opt.symbol,
                'strike_price': opt.strike_price,
                'expiration_date': opt.expiration_date.strftime('%Y-%m-%d'),
                'contract_type': 'call' if opt.type == 'call' else 'put',
                'delta': None  # Alpaca doesn't provide delta directly
            } for opt in filtered_options]
            
        except Exception as e:
            logger.error(f"Error getting option contracts for {ticker}: {e}")
            return []
    
    def get_option_quotes(self, option_symbol: str) -> Optional[Dict]:
        """Get real-time quote for an option contract"""
        if not self.trading_client:
            logger.error("Trading client not initialized")
            return None
            
        try:
            # Get latest quote using the trading client
            quote = self.trading_client.get_latest_quote(option_symbol)
            
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
    
    def get_real_time_data(self, symbols: List[str] = TRADING_SYMBOLS) -> Dict:
        """Get real-time data for a list of symbols"""
        quotes = {}
        
        for symbol in symbols:
            quote = self.get_latest_quote(symbol)
            if quote:
                quotes[symbol] = quote
        
        return quotes
    
    def _create_fallback_data(self, symbol: str, days_back: int) -> pd.DataFrame:
        """Create fallback data when API calls fail"""
        try:
            # Create a simple DataFrame with random data
            dates = pd.date_range(end=datetime.now(), periods=days_back, freq='D')
            data = {
                'date': dates,
                'open': [100.0] * days_back,
                'high': [101.0] * days_back,
                'low': [99.0] * days_back,
                'close': [100.0] * days_back,
                'volume': [1000000] * days_back
            }
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error creating fallback data: {e}")
            return pd.DataFrame()

    def get_option_historical(self, option_symbol: str, from_date: str, to_date: str, 
                            timespan: str = 'day') -> pd.DataFrame:
        """Get historical data for an option contract"""
        if not self.stock_hist_client:
            logger.error("Historical client not initialized")
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
            bars_request = StockBarsRequest(
                symbol_or_symbols=option_symbol,
                timeframe=alpaca_timeframe,
                start=datetime.strptime(from_date, '%Y-%m-%d'),
                end=datetime.strptime(to_date, '%Y-%m-%d'),
                limit=100 * adjustment_factor if adjustment_factor > 1 else 100
            )
            
            # Get the data
            bars_response = self.stock_hist_client.get_stock_bars(bars_request)
            
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

    def get_historical_data(self, symbol: str, timeframe: str = '1d', 
                          days_back: int = 30) -> Dict[str, List]:
        """
        Get historical price data for a symbol.
        
        Args:
            symbol: The stock symbol
            timeframe: The timeframe for the data (1d, 1h, 4h)
            days_back: Number of days of historical data to fetch
            
        Returns:
            Dictionary containing lists of prices, volumes, and timestamps
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            df = self.get_historical_bars(
                symbol=symbol,
                timeframe=timeframe,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d')
            )
            
            if df.empty:
                logger.warning(f"No historical data found for {symbol}")
                return {'prices': [], 'volumes': [], 'timestamps': []}
                
            logger.info(f"Fetched {len(df)} bars of historical data for {symbol}")
            return {
                'prices': df['close'].tolist(),
                'volumes': df['volume'].tolist(),
                'timestamps': df.index.tolist()
            }
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return {'prices': [], 'volumes': [], 'timestamps': []}
