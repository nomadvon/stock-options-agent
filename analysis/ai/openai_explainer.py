import logging
import os
from typing import Dict, Any
import openai

logger = logging.getLogger(__name__)

class OpenAIExplainer:
    """Class for generating AI explanations of trading signals using OpenAI"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the OpenAI explainer
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        openai.api_key = self.api_key
        logger.info("OpenAI Explainer initialized")
        
    def explain_signal(self, symbol: str, price: float, 
                      technical_analysis: Dict[str, Any],
                      sentiment_analysis: float) -> str:
        """
        Generate an explanation for a trading signal
        
        Args:
            symbol: Stock symbol
            price: Current price
            technical_analysis: Technical analysis results
            sentiment_analysis: Sentiment score (-1 to 1)
            
        Returns:
            str: Generated explanation
        """
        try:
            # Prepare the prompt
            prompt = self._create_prompt(symbol, price, technical_analysis, sentiment_analysis)
            
            # Generate explanation using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional trading analyst explaining trading signals."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.info(f"Generated explanation for {symbol}")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Unable to generate explanation at this time."
            
    def _create_prompt(self, symbol: str, price: float,
                      technical_analysis: Dict[str, Any],
                      sentiment_analysis: float) -> str:
        """Create the prompt for the OpenAI API"""
        return f"""
        Please analyze and explain the following trading signal for {symbol}:
        
        Current Price: ${price:.2f}
        
        Technical Analysis:
        - Box Detected: {technical_analysis.get('box_detected', False)}
        - Box Top: ${technical_analysis.get('box_top', 0.00):.2f}
        - Box Bottom: ${technical_analysis.get('box_bottom', 0.00):.2f}
        - Breakout Direction: {technical_analysis.get('breakout_direction', 'None')}
        - Volume Confirmation: {technical_analysis.get('volume_confirmation', False)}
        
        Sentiment Analysis Score: {sentiment_analysis:.2f}
        
        Please provide a concise explanation of why this might be a good trading opportunity,
        considering both the technical and sentiment factors.
        """ 