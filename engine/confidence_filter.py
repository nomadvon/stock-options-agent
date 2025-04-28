import logging

logger = logging.getLogger(__name__)

class ConfidenceFilter:
    """Filters signals based on confidence levels and additional criteria"""
    
    def apply_filters(self, symbol, direction, confidence, sentiment_data, technical_data):
        """Apply filters to determine if signal should be acted upon"""
        result = {
            'pass': True,
            'reason': None
        }
        
        # For development, we'll use a simplified filter that passes most signals
        # We'll just check for extremely low confidence
        if confidence < 0.3:
            result['pass'] = False
            result['reason'] = f"Confidence too low: {confidence:.2f}"
            return result
            
        # Check minimum article count for sentiment if available
        if sentiment_data and 'article_count' in sentiment_data:
            if sentiment_data['article_count'] < 2:
                result['pass'] = False
                result['reason'] = f"Insufficient news coverage: {sentiment_data['article_count']} articles"
                return result
        
        # Check for conflicting signals across timeframes
        if technical_data:
            conflicting = self._check_conflicting_timeframes(technical_data, direction)
            if conflicting:
                result['pass'] = False
                result['reason'] = "Conflicting signals across timeframes"
                return result
        
        # All filters passed
        return result
    
    def _check_conflicting_timeframes(self, technical_data, direction):
        """Check if there are conflicting signals across different timeframes"""
        # For bullish signal, check if any timeframe is strongly bearish
        # For bearish signal, check if any timeframe is strongly bullish
        timeframe_directions = {}
        
        for timeframe, data in technical_data.items():
            if 'bullish_signals' in data and 'bearish_signals' in data:
                bulls = data['bullish_signals']
                bears = data['bearish_signals']
                
                if bulls > bears * 2:  # Strongly bullish
                    timeframe_directions[timeframe] = 'bullish'
                elif bears > bulls * 2:  # Strongly bearish
                    timeframe_directions[timeframe] = 'bearish'
                else:
                    timeframe_directions[timeframe] = 'neutral'
        
        # Check if we have both strongly bullish and strongly bearish signals
        has_bullish = any(d == 'bullish' for d in timeframe_directions.values())
        has_bearish = any(d == 'bearish' for d in timeframe_directions.values())
        
        if has_bullish and has_bearish:
            return True
            
        # Check if the signal direction conflicts with a strong signal in a timeframe
        if direction == 'bullish' and has_bearish:
            return True
        if direction == 'bearish' and has_bullish:
            return True
            
        return False
