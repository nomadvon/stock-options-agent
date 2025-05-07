import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from .box_analyzer import BoxAnalyzer

class TechnicalAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.box_analyzer = BoxAnalyzer()
        
        # Initialize other technical indicators
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bollinger_period = 20
        self.bollinger_std = 2
        
        self.logger.info("Technical Analyzer initialized with Box Method strategy")

    def analyze(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze price data using technical indicators and Box Method.
        
        Args:
            symbol: Trading symbol
            data: Dictionary containing price and volume data
            
        Returns:
            Dictionary containing analysis results
        """
        prices = data.get('prices', [])
        volumes = data.get('volumes', [])
        timestamps = data.get('timestamps', [])
        
        if not prices or len(prices) < 30:  # Need enough data for all indicators
            return {}
            
        # Convert to numpy arrays for calculations
        prices_np = np.array(prices)
        
        # Calculate traditional technical indicators
        rsi = self._calculate_rsi(prices_np)
        macd, signal = self._calculate_macd(prices_np)
        upper_band, lower_band = self._calculate_bollinger_bands(prices_np)
        
        # Detect box formations
        box_result = self.box_analyzer.detect_box(prices, volumes, timestamps)
        
        analysis = {
            'symbol': symbol,
            'current_price': prices[-1],
            'rsi': rsi[-1],
            'macd': macd[-1],
            'macd_signal': signal[-1],
            'bollinger_upper': upper_band[-1],
            'bollinger_lower': lower_band[-1],
            'box_detected': box_result is not None
        }
        
        if box_result:
            box_top, box_bottom, breakout_price, breakout_volume = box_result
            analysis.update({
                'box_top': box_top,
                'box_bottom': box_bottom,
                'breakout_price': breakout_price,
                'breakout_volume': breakout_volume,
                'is_breakout_up': breakout_price > box_top,
                'is_breakout_down': breakout_price < box_bottom
            })
            
            # Calculate position sizing and take profits
            is_long = breakout_price > box_top
            stop_loss = box_bottom - (box_bottom * self.box_analyzer.stop_loss_tolerance) if is_long else \
                       box_top + (box_top * self.box_analyzer.stop_loss_tolerance)
                       
            num_contracts, risk_amount = self.box_analyzer.calculate_position_size(
                breakout_price, stop_loss, 1000  # Assuming $1000 account value
            )
            
            take_profits = self.box_analyzer.calculate_take_profits(
                breakout_price, stop_loss, is_long
            )
            
            analysis.update({
                'stop_loss': stop_loss,
                'position_size': num_contracts,
                'risk_amount': risk_amount,
                'take_profits': take_profits
            })
        
        return analysis

    def _calculate_rsi(self, prices: np.ndarray) -> np.ndarray:
        """Calculate Relative Strength Index"""
        deltas = np.diff(prices)
        seed = deltas[:self.rsi_period+1]
        up = seed[seed >= 0].sum()/self.rsi_period
        down = -seed[seed < 0].sum()/self.rsi_period
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:self.rsi_period] = 100. - 100./(1.+rs)

        for i in range(self.rsi_period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(self.rsi_period-1) + upval)/self.rsi_period
            down = (down*(self.rsi_period-1) + downval)/self.rsi_period
            rs = up/down
            rsi[i] = 100. - 100./(1.+rs)

        return rsi

    def _calculate_macd(self, prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate MACD"""
        exp1 = np.convolve(prices, np.ones(self.macd_fast)/self.macd_fast, mode='valid')
        exp2 = np.convolve(prices, np.ones(self.macd_slow)/self.macd_slow, mode='valid')
        macd = exp1[-len(exp2):] - exp2
        signal = np.convolve(macd, np.ones(self.macd_signal)/self.macd_signal, mode='valid')
        return macd, signal

    def _calculate_bollinger_bands(self, prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate Bollinger Bands"""
        sma = np.convolve(prices, np.ones(self.bollinger_period)/self.bollinger_period, mode='valid')
        std = np.array([np.std(prices[i-self.bollinger_period:i]) 
                       for i in range(self.bollinger_period, len(prices)+1)])
        upper_band = sma + (std * self.bollinger_std)
        lower_band = sma - (std * self.bollinger_std)
        return upper_band, lower_band 