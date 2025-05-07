import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os

import openai
from events.event_queue import EventQueue, Event, EventPriority
from alerts.discord_webhook import DiscordWebhook

logger = logging.getLogger(__name__)

class SignalGenerator:
    """Generates trading signals using OpenAI"""
    
    def __init__(self, event_queue: EventQueue, openai_api_key: str):
        self.event_queue = event_queue
        # Set the API key in the environment
        os.environ["OPENAI_API_KEY"] = openai_api_key
        openai.api_key = openai_api_key
        self.discord_webhook = DiscordWebhook()
        self.model = "gpt-3.5-turbo"
        self.last_signals: Dict[str, datetime] = {}
        self.min_signal_interval = 3600  # Minimum 1 hour between signals for same symbol
        
    async def start(self):
        """Start generating signals"""
        # Register event handler
        self.event_queue.register_handler("trading_signal", self._handle_trading_signal)
        
    async def _handle_trading_signal(self, event: Event):
        """Handle trading signal events"""
        try:
            symbol = event.data["symbol"]
            technical_data = event.data["technical_data"]
            sentiment_data = event.data["sentiment_data"]
            
            # Check if we've sent a signal recently
            if symbol in self.last_signals:
                time_since_last = (datetime.now() - self.last_signals[symbol]).total_seconds()
                if time_since_last < self.min_signal_interval:
                    return
                    
            # Generate signal using OpenAI
            signal = await self._generate_signal(symbol, technical_data, sentiment_data)
            
            if signal:
                # Send Discord notification
                await self._send_discord_notification(symbol, signal)
                
                # Update last signal time
                self.last_signals[symbol] = datetime.now()
                
        except Exception as e:
            logger.error(f"Error handling trading signal: {e}")
            
    async def _generate_signal(self, symbol: str, technical_data: Dict[str, Any], sentiment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a trading signal using OpenAI"""
        try:
            # Format the data into a clear prompt
            prompt = (
                f"Analyze {symbol} for options swing trading using the box method. Provide specific entry/exit points and a brief analysis.\n\n"
                f"Technical Data:\n"
                f"RSI: {technical_data.get('rsi', 'N/A')} (Relative Strength Index - measures overbought/oversold conditions)\n"
                f"MACD: {technical_data.get('macd', 'N/A')} (Moving Average Convergence Divergence - trend momentum)\n"
                f"Bollinger Bands: {technical_data.get('bollinger_bands', {}).get('upper', 'N/A')} | {technical_data.get('bollinger_bands', {}).get('middle', 'N/A')} | {technical_data.get('bollinger_bands', {}).get('lower', 'N/A')} (Price volatility bands)\n"
                f"Sentiment: {sentiment_data.get('sentiment_label', 'N/A')} ({sentiment_data.get('overall_score', 'N/A')})\n\n"
                f"Provide:\n"
                f"1. Clear entry/exit points using the box method\n"
                f"2. Brief technical analysis (max 2 sentences)\n"
                f"3. Beginner-friendly explanation (2-3 sentences):\n"
                f"   - Explain what the analysis means in simple terms\n"
                f"   - Avoid technical jargon\n"
                f"   - Use analogies if helpful (e.g., 'like a rubber band stretching')\n"
                f"   - Explain why we're choosing calls or puts\n"
                f"4. Confidence level (High/Medium/Low) with a simple reason why\n"
                f"5. Key price levels to watch\n"
                f"Format as JSON with keys: entry_points, exit_points, analysis, simplified_analysis, confidence, confidence_reason, key_levels"
            )
            
            # Get AI analysis
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert options trader explaining complex concepts to complete beginners. Use simple language, analogies, and clear explanations that anyone can understand. Avoid technical jargon, and when you must use it, explain what it means in plain English."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            # Parse the response
            analysis_str = response.choices[0].message.content
            analysis = json.loads(analysis_str)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None
            
    async def _send_discord_notification(self, symbol: str, signal: Dict[str, Any]):
        """Send a Discord notification for the trading signal"""
        try:
            # Get current price
            current_price = signal.get("current_price", 0)
            
            # Determine option type
            option_type = "call" if signal.get("analysis", "").lower().find("bullish") != -1 else "put"
            
            # Get expiration date (next Friday)
            today = datetime.now()
            days_ahead = 4 - today.weekday()  # 4 is Friday
            if days_ahead <= 0:  # If today is Friday or later in the week
                days_ahead += 7
            expiration_date = (today + timedelta(days=days_ahead)).strftime('%m-%d-%y')
            
            # Calculate premium (simplified)
            premium = current_price * 0.02  # 2% of current price
            
            # Send Discord notification
            await self.discord_webhook.send_options_signal(
                symbol=symbol,
                current_price=current_price,
                option_type=option_type,
                expiration_date=expiration_date,
                premium=premium,
                ai_analysis=json.dumps(signal)
            )
            
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}") 