import logging
import numpy as np
from datetime import datetime

from config.config import (SENTIMENT_WEIGHT, TECHNICAL_WEIGHT, 
                          SIGNAL_THRESHOLD, STOP_LOSS_LEVELS, TAKE_PROFIT_LEVELS)
from engine.confidence_filter import ConfidenceFilter
from engine.trade_formatter import TradeFormatter

logger = logging.getLogger(__name__)

class SignalEngine:
    """Combines technical and sentiment signals to generate trade signals"""
    
    def __init__(self, sentiment_weight=SENTIMENT_WEIGHT, 
                technical_weight=TECHNICAL_WEIGHT,
                signal_threshold=SIGNAL_THRESHOLD):
        self.sentiment_weight = sentiment_weight
        self.technical_weight = technical_weight
        self.signal_threshold = signal_threshold
        self.confidence_filter = ConfidenceFilter()
        self.trade_formatter = TradeFormatter()
    
    def _calculate_signal_score(self, sentiment_data, technical_data):
        """Calculate a combined signal score from sentiment and technical data"""
        # Default scores
        sentiment_score = 0.5  # Neutral
        technical_score = 0.5  # Neutral
        
        # Process sentiment data if available
        if sentiment_data and 'overall_score' in sentiment_data:
            # Sentiment score is typically from -1 to 1, normalize to 0 to 1
            sentiment_score = (sentiment_data['overall_score'] + 1) / 2
        
        # Process technical data if available
        if technical_data:
            # Calculate average bullish vs bearish signals across timeframes
            bullish_signals = 0
            bearish_signals = 0
            timeframe_count = 0
            
            for timeframe, data in technical_data.items():
                if 'bullish_signals' in data and 'bearish_signals' in data:
                    bullish_signals += data['bullish_signals']
                    bearish_signals += data['bearish_signals']
                    timeframe_count += 1
            
            if timeframe_count > 0:
                total_signals = bullish_signals + bearish_signals
                if total_signals > 0:
                    # Normalize to 0 to 1 range
                    technical_score = bullish_signals / total_signals
        
        # Combine scores using weights
        combined_score = (sentiment_score * self.sentiment_weight + 
                         technical_score * self.technical_weight)
        
        # Ensure score stays in valid range
        combined_score = max(min(combined_score, 1.0), 0.0)
        
        return {
            'combined': combined_score,
            'sentiment': sentiment_score,
            'technical': technical_score
        }
    
    def _determine_signal_direction(self, score):
        """Determine if signal is bullish or bearish based on score"""
        # If score > 0.5, bullish signal (calls)
        # If score < 0.5, bearish signal (puts)
        # Score is exactly 0.5 would be neutral, but we'll default to bullish for simplicity
        if score >= 0.5:
            return 'bullish', 'call'
        else:
            return 'bearish', 'put'
    
    def generate_signals(self, symbol, sentiment_data, technical_data):
        """Generate trade signals for a symbol"""
        logger.info(f"Generating signals for {symbol}")
        
        try:
            # Calculate signal score
            scores = self._calculate_signal_score(sentiment_data, technical_data)
            combined_score = scores['combined']
            
            # Normalize score to confidence level (0 to 1)
            # We'll use the distance from 0.5 as confidence
            confidence = abs(combined_score - 0.5) * 2
            
            # Determine signal direction
            direction, option_type = self._determine_signal_direction(combined_score)
            
            # Check if signal meets threshold
            if confidence < self.signal_threshold:
                logger.info(f"Signal for {symbol} below threshold: {confidence:.2f} < {self.signal_threshold}")
                return []
            
            # Apply confidence filtering
            confidence_result = self.confidence_filter.apply_filters(symbol, direction, confidence, 
                                                                   sentiment_data, technical_data)
            
            if not confidence_result['pass']:
                logger.info(f"Signal for {symbol} filtered out: {confidence_result['reason']}")
                return []
            
            # Create signal
            signal = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'direction': direction,
                'option_type': option_type,
                'confidence': confidence,
                'sentiment_score': scores['sentiment'],
                'technical_score': scores['technical'],
                'stop_loss_levels': STOP_LOSS_LEVELS,
                'take_profit_levels': TAKE_PROFIT_LEVELS,
                'holding_period': '1-10 days',  # Swing trade
                'analysis': {
                    'sentiment': sentiment_data,
                    'technical': technical_data
                }
            }
            
            # Format the signal for output
            formatted_signal = self.trade_formatter.format_trade_signal(signal)
            
            return [formatted_signal]
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}", exc_info=True)
            return []
