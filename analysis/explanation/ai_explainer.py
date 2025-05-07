import logging
from typing import Dict, Any
import os

class AIExplainer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        self.logger.info("AIExplainer initialized")

    def explain_signal(self, symbol: str, price: float, 
                      technical_analysis: Dict[str, Any],
                      sentiment_analysis: float) -> str:
        """
        Generate a human-readable explanation for a trading signal.
        
        Args:
            symbol: Trading symbol
            price: Current price
            technical_analysis: Technical analysis results
            sentiment_analysis: Sentiment score
            
        Returns:
            String explanation of the trading signal
        """
        try:
            # Extract box information
            box_top = technical_analysis.get('box_top', 0)
            box_bottom = technical_analysis.get('box_bottom', 0)
            box_range = ((box_top - box_bottom) / box_bottom) * 100
            breakout_volume = technical_analysis.get('breakout_volume', 0)
            is_breakout_up = technical_analysis.get('is_breakout_up', False)
            
            # Format sentiment description
            if sentiment_analysis > 0.3:
                sentiment_desc = "bullish"
            elif sentiment_analysis < -0.3:
                sentiment_desc = "bearish"
            else:
                sentiment_desc = "neutral"
                
            # Generate explanation
            explanation = (
                f"Technical Analysis:\n"
                f"- Box consolidation detected between ${box_bottom:.2f} and ${box_top:.2f} "
                f"(range: {box_range:.1f}%)\n"
                f"- {'Bullish breakout above' if is_breakout_up else 'Bearish breakout below'} "
                f"the box with increased volume ({breakout_volume:,.0f} shares)\n"
                f"- Current price at ${price:.2f}\n\n"
                f"Sentiment Analysis:\n"
                f"- Market sentiment is {sentiment_desc} (score: {sentiment_analysis:.2f})\n"
                f"- This {'supports' if (sentiment_analysis > 0) == is_breakout_up else 'contradicts'} "
                f"the technical signal"
            )
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error generating explanation: {str(e)}")
            return "Unable to generate explanation due to an error" 