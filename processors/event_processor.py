import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from analysis.technical.technical_analysis import TechnicalAnalyzer
from analysis.sentiment.finbert_analyzer import FinBERTAnalyzer
from events.event_queue import EventQueue, Event, EventPriority

logger = logging.getLogger(__name__)

class EventProcessor:
    """Processes events and generates trading signals"""
    
    def __init__(self, event_queue: EventQueue):
        self.event_queue = event_queue
        self.technical_analyzer = TechnicalAnalyzer()
        self.sentiment_analyzer = FinBERTAnalyzer()
        self.price_history: Dict[str, list[float]] = {}
        self.sentiment_history: Dict[str, list[float]] = {}
        self.max_history = 100  # Keep last 100 data points
        self.running = False
        
    async def start(self):
        """Start processing events"""
        self.running = True
        # Register event handlers
        self.event_queue.register_handler("price_update", self._handle_price_update)
        self.event_queue.register_handler("news_update", self._handle_news_update)
        
    async def stop(self):
        """Stop processing events"""
        self.running = False
        logger.info("Stopping event processor")
        
    async def _handle_price_update(self, event: Event):
        """Handle price update events"""
        try:
            symbol = event.data["symbol"]
            price = event.data["price"]
            
            # Update price history
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            self.price_history[symbol].append(price)
            if len(self.price_history[symbol]) > self.max_history:
                self.price_history[symbol].pop(0)
                
            # Get technical analysis
            technical_data = self.technical_analyzer.analyze(symbol)
            
            # Check for significant technical signals
            if self._has_significant_technical_signal(technical_data):
                # Get sentiment analysis
                sentiment_data = self.sentiment_analyzer.get_ticker_sentiment(symbol)
                
                # Generate trading signal
                await self._generate_trading_signal(symbol, technical_data, sentiment_data)
                
        except Exception as e:
            logger.error(f"Error handling price update: {e}")
            
    async def _handle_news_update(self, event: Event):
        """Handle news update events"""
        try:
            symbol = event.data["symbol"]
            article = event.data["article"]
            sentiment = article["sentiment"]
            
            # Update sentiment history
            if symbol not in self.sentiment_history:
                self.sentiment_history[symbol] = []
            self.sentiment_history[symbol].append(sentiment)
            if len(self.sentiment_history[symbol]) > self.max_history:
                self.sentiment_history[symbol].pop(0)
                
            # Check for significant sentiment change
            if self._has_significant_sentiment_change(symbol):
                # Get technical analysis
                technical_data = self.technical_analyzer.analyze(symbol)
                
                # Generate trading signal
                await self._generate_trading_signal(symbol, technical_data, {
                    "overall_score": sum(self.sentiment_history[symbol]) / len(self.sentiment_history[symbol]),
                    "sentiment_label": "positive" if sum(self.sentiment_history[symbol]) > 0 else "negative"
                })
                
        except Exception as e:
            logger.error(f"Error handling news update: {e}")
            
    def _has_significant_technical_signal(self, technical_data: Dict[str, Any]) -> bool:
        """Check if technical data shows significant signals"""
        try:
            # Check RSI
            rsi = technical_data.get("rsi", 50)
            if rsi < 30 or rsi > 70:  # Overbought/oversold
                return True
                
            # Check MACD
            macd = technical_data.get("macd", 0)
            if abs(macd) > 2:  # Strong momentum
                return True
                
            # Check Bollinger Bands
            bb = technical_data.get("bollinger_bands", {})
            if bb:
                upper = bb.get("upper", 0)
                lower = bb.get("lower", 0)
                middle = bb.get("middle", 0)
                current_price = technical_data.get("current_price", 0)
                
                if abs(current_price - upper) < (upper - middle) * 0.1 or \
                   abs(current_price - lower) < (middle - lower) * 0.1:
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking technical signals: {e}")
            return False
            
    def _has_significant_sentiment_change(self, symbol: str) -> bool:
        """Check if sentiment has changed significantly"""
        try:
            if symbol not in self.sentiment_history or len(self.sentiment_history[symbol]) < 2:
                return False
                
            # Calculate average sentiment change
            changes = []
            for i in range(1, len(self.sentiment_history[symbol])):
                change = abs(self.sentiment_history[symbol][i] - self.sentiment_history[symbol][i-1])
                changes.append(change)
                
            avg_change = sum(changes) / len(changes)
            return avg_change > 0.2  # Significant change threshold
            
        except Exception as e:
            logger.error(f"Error checking sentiment change: {e}")
            return False
            
    async def _generate_trading_signal(self, symbol: str, technical_data: Dict[str, Any], sentiment_data: Dict[str, Any]):
        """Generate a trading signal event"""
        try:
            # Create trading signal event
            event = Event(
                event_type="trading_signal",
                data={
                    "symbol": symbol,
                    "technical_data": technical_data,
                    "sentiment_data": sentiment_data,
                    "timestamp": datetime.now().isoformat()
                },
                priority=EventPriority.HIGH,
                timestamp=datetime.now(),
                source="event_processor"
            )
            
            # Publish the event
            await self.event_queue.publish(event)
            
        except Exception as e:
            logger.error(f"Error generating trading signal: {e}") 