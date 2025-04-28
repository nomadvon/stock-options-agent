import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from config.config import TRADING_SYMBOLS, TECHNICAL_TIMEFRAMES
from data.polygon_connector import PolygonConnector

logger = logging.getLogger(__name__)

class TechnicalAnalysis:
    """Technical analysis for stocks (simplified for development)"""
    
    def __init__(self):
        self.polygon = PolygonConnector()
        
    def fetch_historical_data(self, symbol, timeframe='1d', days_back=30):
        """Fetch historical price data for technical analysis"""
        today = datetime.now()
        from_date = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')
        to_date = today.strftime('%Y-%m-%d')
        
        try:
            # For development, we'll use a simplified approach
            # that creates mock data instead of fetching from the API
            # This helps avoid API rate limits during testing
            
            # Create a date range
            date_range = pd.date_range(end=today, periods=days_back)
            
            # Create mock data with a slight uptrend
            base_price = 100  # Starting price
            if symbol == 'AAPL':
                base_price = 180
            elif symbol == 'MSFT':
                base_price = 420
            elif symbol == 'NVDA':
                base_price = 950
                
            # Generate random price movements with a slight uptrend
            np.random.seed(42)  # For reproducibility
            daily_returns = np.random.normal(0.001, 0.02, days_back)  # Mean 0.1%, std 2%
            cumulative_returns = np.cumprod(1 + daily_returns)
            
            # Create OHLC data
            close_prices = base_price * cumulative_returns
            high_prices = close_prices * (1 + np.random.uniform(0, 0.02, days_back))
            low_prices = close_prices * (1 - np.random.uniform(0, 0.02, days_back))
            open_prices = low_prices + np.random.uniform(0, 1, days_back) * (high_prices - low_prices)
            
            # Create volume data (in millions)
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
            
            # Sort by date
            df = df.sort_values('date')
            
            logger.info(f"Created mock historical data for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error creating mock data for {symbol}: {e}")
            return None
    
    def calculate_indicators(self, df):
        """Calculate technical indicators for a dataframe"""
        if df is None or df.empty:
            return None
        
        try:
            # Make a copy to avoid modifying the original
            df = df.copy()
            
            # RSI (Relative Strength Index)
            # Simple implementation for development
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            rs = avg_gain / avg_loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Moving Averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            
            # MACD
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_std'] = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
            df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
    
    def get_technical_signals(self, ticker, timeframes=TECHNICAL_TIMEFRAMES):
        """Get technical signals for a ticker across multiple timeframes"""
        signals = {}
        
        for timeframe in timeframes:
            try:
                # Fetch and process data
                df = self.fetch_historical_data(ticker, timeframe)
                if df is None:
                    continue
                    
                df = self.calculate_indicators(df)
                if df is None:
                    continue
                
                # Get the most recent values
                latest = df.iloc[-1].to_dict()
                prev = df.iloc[-2].to_dict() if len(df) > 1 else None
                
                # Initialize signals for this timeframe
                signals[timeframe] = {
                    'bullish_signals': 0,
                    'bearish_signals': 0,
                    'neutral_signals': 0,
                    'indicators': {}
                }
                
                # RSI signals
                if 'rsi' in latest and not np.isnan(latest['rsi']):
                    if latest['rsi'] < 30:
                        signals[timeframe]['bullish_signals'] += 1
                        signals[timeframe]['indicators']['rsi'] = {
                            'value': float(latest['rsi']),
                            'signal': 'bullish',
                            'desc': 'Oversold'
                        }
                    elif latest['rsi'] > 70:
                        signals[timeframe]['bearish_signals'] += 1
                        signals[timeframe]['indicators']['rsi'] = {
                            'value': float(latest['rsi']),
                            'signal': 'bearish',
                            'desc': 'Overbought'
                        }
                    else:
                        signals[timeframe]['neutral_signals'] += 1
                        signals[timeframe]['indicators']['rsi'] = {
                            'value': float(latest['rsi']),
                            'signal': 'neutral',
                            'desc': 'Neutral'
                        }
                
                # MACD signals
                if 'macd' in latest and 'macd_signal' in latest and prev:
                    if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                        signals[timeframe]['bullish_signals'] += 1
                        signals[timeframe]['indicators']['macd'] = {
                            'value': float(latest['macd']),
                            'signal': 'bullish',
                            'desc': 'Bullish crossover'
                        }
                    elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                        signals[timeframe]['bearish_signals'] += 1
                        signals[timeframe]['indicators']['macd'] = {
                            'value': float(latest['macd']),
                            'signal': 'bearish',
                            'desc': 'Bearish crossover'
                        }
                    elif latest['macd'] > latest['macd_signal']:
                        signals[timeframe]['bullish_signals'] += 1
                        signals[timeframe]['indicators']['macd'] = {
                            'value': float(latest['macd']),
                            'signal': 'bullish',
                            'desc': 'Bullish'
                        }
                    elif latest['macd'] < latest['macd_signal']:
                        signals[timeframe]['bearish_signals'] += 1
                        signals[timeframe]['indicators']['macd'] = {
                            'value': float(latest['macd']),
                            'signal': 'bearish',
                            'desc': 'Bearish'
                        }
                
                # Moving Average signals
                if 'ema_9' in latest and 'sma_20' in latest:
                    if latest['ema_9'] > latest['sma_20']:
                        signals[timeframe]['bullish_signals'] += 1
                        signals[timeframe]['indicators']['ma_cross'] = {
                            'value': float(latest['ema_9'] - latest['sma_20']),
                            'signal': 'bullish',
                            'desc': 'EMA 9 above SMA 20'
                        }
                    else:
                        signals[timeframe]['bearish_signals'] += 1
                        signals[timeframe]['indicators']['ma_cross'] = {
                            'value': float(latest['ema_9'] - latest['sma_20']),
                            'signal': 'bearish',
                            'desc': 'EMA 9 below SMA 20'
                        }
                
                # Bollinger Bands signals
                if all(k in latest for k in ['close', 'bb_upper', 'bb_lower', 'bb_middle']):
                    if latest['close'] > latest['bb_upper']:
                        signals[timeframe]['bearish_signals'] += 1
                        signals[timeframe]['indicators']['bbands'] = {
                            'value': float(latest['close']),
                            'signal': 'bearish',
                            'desc': 'Price above upper band'
                        }
                    elif latest['close'] < latest['bb_lower']:
                        signals[timeframe]['bullish_signals'] += 1
                        signals[timeframe]['indicators']['bbands'] = {
                            'value': float(latest['close']),
                            'signal': 'bullish',
                            'desc': 'Price below lower band'
                        }
                    else:
                        signals[timeframe]['neutral_signals'] += 1
                        signals[timeframe]['indicators']['bbands'] = {
                            'value': float(latest['close']),
                            'signal': 'neutral',
                            'desc': 'Price within bands'
                        }
                
            except Exception as e:
                logger.error(f"Error processing {timeframe} timeframe for {ticker}: {e}")
                continue
        
        return signals
