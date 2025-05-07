import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from analysis.sentiment.finbert_analyzer import FinBERTAnalyzer
from events.event_queue import EventQueue

logger = logging.getLogger(__name__)

class NewsMonitor:
    """Monitors news and publishes sentiment events 24/7"""
    
    def __init__(self, event_queue: EventQueue):
        self.event_queue = event_queue
        self.analyzer = FinBERTAnalyzer()
        self.checked_articles: Dict[str, set] = {}
        self.running = False
        self.last_check: Dict[str, datetime] = {}
        
    async def start(self, symbols: List[str]):
        """Start monitoring news for given symbols"""
        self.running = True
        for symbol in symbols:
            self.checked_articles[symbol] = set()
            self.last_check[symbol] = datetime.now()
        logger.info(f"Starting 24/7 news monitoring for symbols: {', '.join(symbols)}")
        asyncio.create_task(self._monitor_news(symbols))
        
    async def stop(self):
        """Stop monitoring news"""
        self.running = False
        logger.info("Stopping news monitoring")
        
    async def _monitor_news(self, symbols: List[str]):
        """Continuously monitor news for symbols"""
        while self.running:
            try:
                for symbol in symbols:
                    try:
                        # Get sentiment for the symbol
                        sentiment = self.analyzer.get_ticker_sentiment(symbol)
                        
                        # Publish sentiment event
                        await self.event_queue.publish_news_update(
                            symbol=symbol,
                            article={"sentiment": sentiment}
                        )
                        
                        self.last_check[symbol] = datetime.now()
                        logger.info(f"Updated news sentiment for {symbol}: {sentiment['overall_score']:.2f}")
                        
                    except Exception as e:
                        logger.error(f"Error processing news for {symbol}: {e}")
                        continue  # Continue with next symbol even if one fails
                    
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in news monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying 