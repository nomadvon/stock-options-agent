import logging
import yfinance as yf
import numpy as np
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """Analyzes technical indicators for trading signals"""
    
    def __init__(self):
        pass
    
    def _calculate_rsi(self, data: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]
    
    def _calculate_macd(self, data: pd.Series) -> float:
        """Calculate MACD"""
        exp1 = data.ewm(span=12, adjust=False).mean()
        exp2 = data.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return (macd - signal).iloc[-1]
    
    def _calculate_bollinger_bands(self, data: pd.Series, period: int = 20) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        return {
            "upper": upper.iloc[-1],
            "middle": sma.iloc[-1],
            "lower": lower.iloc[-1]
        }
    
    def analyze(self, symbol: str) -> Dict[str, Any]:
        """Analyze technical indicators for a given symbol"""
        try:
            logger.info(f"Analyzing technical indicators for {symbol}")
            
            # Get historical data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo", interval="1d")
            
            if hist.empty:
                logger.error(f"No historical data found for {symbol}")
                return {}
            
            # Calculate indicators
            close_prices = hist['Close']
            
            rsi = self._calculate_rsi(close_prices)
            macd = self._calculate_macd(close_prices)
            bollinger_bands = self._calculate_bollinger_bands(close_prices)
            
            return {
                "rsi": round(rsi, 2),
                "macd": round(macd, 2),
                "bollinger_bands": {
                    "upper": round(bollinger_bands["upper"], 2),
                    "middle": round(bollinger_bands["middle"], 2),
                    "lower": round(bollinger_bands["lower"], 2)
                }
            }
        except Exception as e:
            logger.error(f"Error in technical analysis for {symbol}: {e}")
            return {} 