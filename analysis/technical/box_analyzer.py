import logging
from typing import List, Tuple, Optional
import numpy as np
from datetime import datetime, timedelta

class BoxAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Box Method Parameters
        self.box_size_threshold = 0.02  # 2.0% of price range
        self.min_consolidation_candles = 5  # Minimum candles for box
        self.volume_threshold_multiplier = 1.3  # Volume increase for breakout
        self.box_retest_tolerance = 0.005  # 0.5% of box range
        
        # Risk Management Parameters
        self.stop_loss_additional_range = 0.0035  # 0.35% additional range for stop loss (middle of 0.2% to 0.5%)
        self.max_concurrent_trades = 2
        self.risk_per_trade = 25  # $25 risk per trade
        self.risk_reward_ratios = [2, 3, 4]  # Take profit levels
        
        self.logger.info("Box Analyzer initialized with parameters:")
        self.logger.info(f"Box Size Threshold: {self.box_size_threshold*100}%")
        self.logger.info(f"Min Consolidation Candles: {self.min_consolidation_candles}")
        self.logger.info(f"Volume Threshold: {self.volume_threshold_multiplier}x")
        self.logger.info(f"Box Retest Tolerance: {self.box_retest_tolerance*100}%")

    def detect_box(self, prices: List[float], volumes: List[float], 
                  timestamps: List[datetime]) -> Optional[Tuple[float, float, float, float]]:
        """
        Detect a valid box formation in the price data.
        
        Args:
            prices: List of closing prices
            volumes: List of corresponding volumes
            timestamps: List of corresponding timestamps
            
        Returns:
            Tuple of (box_top, box_bottom, breakout_price, breakout_volume) if valid box found,
            None otherwise
        """
        if len(prices) < self.min_consolidation_candles + 1:  # +1 for breakout candle
            self.logger.debug(f"Not enough candles for box detection. Need {self.min_consolidation_candles + 1}, got {len(prices)}")
            return None
            
        # Look for box formation in the last N+1 candles
        window_size = self.min_consolidation_candles + 1
        for i in range(len(prices) - window_size + 1):
            window_prices = prices[i:i+window_size]
            window_volumes = volumes[i:i+window_size]
            
            # Calculate box parameters for the consolidation period (excluding last candle)
            box_prices = window_prices[:-1]
            box_volumes = window_volumes[:-1]
            
            box_high = max(box_prices)
            box_low = min(box_prices)
            box_range = (box_high - box_low) / box_low
            
            # Log box range for debugging
            self.logger.debug(f"Analyzing potential box: Range={box_range*100:.1f}%, "
                            f"High=${box_high:.2f}, Low=${box_low:.2f}")
            
            # Check if price range is within threshold
            if box_range <= self.box_size_threshold:
                # Calculate average volume during consolidation
                avg_volume = np.mean(box_volumes)
                
                # Get breakout candle
                breakout_price = window_prices[-1]
                breakout_volume = window_volumes[-1]
                
                # Check for valid breakout
                is_breakout_up = breakout_price > box_high
                is_breakout_down = breakout_price < box_low
                has_volume = breakout_volume > (avg_volume * self.volume_threshold_multiplier)
                
                # Log breakout conditions
                self.logger.debug(f"Breakout conditions: Up={is_breakout_up}, Down={is_breakout_down}, "
                                f"Volume Increase={breakout_volume/avg_volume:.1f}x")
                
                if (is_breakout_up or is_breakout_down) and has_volume:
                    self.logger.info(f"Box detected: Range={box_range*100:.1f}%, "
                                   f"Volume Increase={breakout_volume/avg_volume:.1f}x, "
                                   f"Direction={'UP' if is_breakout_up else 'DOWN'}")
                    return (box_high, box_low, breakout_price, breakout_volume)
            else:
                self.logger.debug(f"Box range {box_range*100:.1f}% exceeds threshold {self.box_size_threshold*100}%")
        
        return None

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> Tuple[int, float]:
        """
        Calculate position size based on risk parameters.
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            
        Returns:
            Tuple of (number of contracts, risk amount)
        """
        # Calculate price risk per unit
        price_risk = abs(entry_price - stop_loss)
        
        # Calculate position size: Risk amount divided by price risk
        num_contracts = int(self.risk_per_trade / price_risk)
        
        return num_contracts, self.risk_per_trade

    def calculate_stop_loss(self, box_top: float, box_bottom: float, is_long: bool) -> float:
        """
        Calculate stop loss based on box boundaries.
        
        Args:
            box_top: Top of the box
            box_bottom: Bottom of the box
            is_long: Whether the trade is long or short
            
        Returns:
            Stop loss price
        """
        box_range = box_top - box_bottom
        additional_range = box_range * self.stop_loss_additional_range
        
        if is_long:
            # For longs: Stop loss just below box bottom minus additional range
            return box_bottom - additional_range
        else:
            # For shorts: Stop loss just above box top plus additional range
            return box_top + additional_range

    def calculate_take_profits(self, entry_price: float, stop_loss: float, 
                             is_long: bool) -> List[float]:
        """
        Calculate take profit levels based on risk-reward ratios.
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            is_long: Whether the trade is long or short
            
        Returns:
            List of take profit prices
        """
        risk = abs(entry_price - stop_loss)
        take_profits = []
        
        for ratio in self.risk_reward_ratios:
            if is_long:
                take_profit = entry_price + (risk * ratio)
            else:
                take_profit = entry_price - (risk * ratio)
            take_profits.append(take_profit)
            
        return take_profits

    def validate_box_retest(self, current_price: float, box_top: float, 
                          box_bottom: float) -> bool:
        """
        Validate if a retest of the box is within acceptable tolerance.
        
        Args:
            current_price: Current price
            box_top: Top of the box
            box_bottom: Bottom of the box
            
        Returns:
            True if retest is valid, False otherwise
        """
        box_range = box_top - box_bottom
        tolerance = box_range * self.box_retest_tolerance
        
        if current_price > box_top:
            return (current_price - box_top) <= tolerance
        elif current_price < box_bottom:
            return (box_bottom - current_price) <= tolerance
            
        return False 