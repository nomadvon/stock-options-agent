import logging
import time
from datetime import datetime
from typing import Dict, Any, List
from config.config import TRADING_SYMBOLS, MARKET_EVENTS_CHECK_INTERVAL_HOURS
from events.event import Event, EventPriority
from events.event_queue import EventQueue
from data.alpaca_connector import AlpacaConnector
from analysis.technical.technical_analyzer import TechnicalAnalyzer
from analysis.sentiment.finbert_analyzer import FinbertAnalyzer
from analysis.ai.openai_explainer import OpenAIExplainer
from utils.discord_webhook import DiscordWebhook
import asyncio

class TradingAgent:
    def __init__(self, event_queue: EventQueue):
        # Setup logging
        self.loggers = {
            'price_action': logging.getLogger('price_action'),
            'box_method': logging.getLogger('box_method'),
            'trades': logging.getLogger('trades'),
            'errors': logging.getLogger('errors')
        }
        
        # Initialize components
        self.event_queue = event_queue
        self.alpaca = AlpacaConnector()
        self.technical_analyzer = TechnicalAnalyzer()
        self.sentiment_analyzer = FinbertAnalyzer()
        self.ai_explainer = OpenAIExplainer()
        self.discord_webhook = DiscordWebhook()
        
        # Track active trades
        self.active_trades = {}
        
        # Subscribe to events
        self._subscribe_to_events()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Trading Agent initialized")

    async def start(self):
        """Start the trading agent"""
        try:
            # Send startup message first
            self.discord_webhook.send_update({
                'type': 'startup',
                'message': 'Options Trading Agent Started in Production Mode'
            })
            
            # No need to start market monitoring here as it's handled by run_production.py
            self.logger.info("Trading agent started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting trading agent: {str(e)}")
            raise

    async def stop(self):
        """Stop the trading agent"""
        try:
            # Send shutdown message
            self.discord_webhook.send_update({
                'type': 'shutdown',
                'message': 'Options Trading Agent Stopped'
            })
            
            logger.info("Trading agent stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping trading agent: {str(e)}")
            raise

    def _subscribe_to_events(self):
        """Subscribe to relevant events"""
        self.event_queue.register_handler("price_update", self._handle_price_update)
        self.event_queue.register_handler("news_update", self._handle_news_update)
        self.event_queue.register_handler("sentiment_update", self._handle_sentiment_update)
        self.event_queue.register_handler("status_update", self._handle_status_event)

    def _handle_status_event(self, event: Event):
        """Handle status update events"""
        try:
            status = event.data.get('status')
            message = event.data.get('message')
            
            if status and message:
                # Send status update to Discord
                self.discord_webhook.send_update({
                    'type': 'status',
                    'status': status,
                    'message': message
                })
                
        except Exception as e:
            self.logger.error(f"Error handling status event: {str(e)}")

    async def _start_market_monitoring(self):
        """Start monitoring market events"""
        while True:
            if self._is_market_open():
                await self._check_market_events()
            await asyncio.sleep(MARKET_EVENTS_CHECK_INTERVAL_HOURS * 3600)

    async def _handle_price_update(self, event: Event):
        """Handle price update events"""
        try:
            symbol = event.data.get('symbol')
            price = event.data.get('price')
            volume = event.data.get('volume')
            
            if not all([symbol, price, volume]):
                return
                
            # Log price action
            price_message = f"Symbol: {symbol}, Price: ${price:.2f}, Volume: {volume:,}"
            self.loggers['price_action'].info(price_message)
            self.discord_webhook.stream_logs('price_action', price_message)
                
            # Get historical data for analysis
            historical_data = self.alpaca.get_historical_data(symbol)
            
            # Analyze using Box Method
            analysis = self.technical_analyzer.analyze(symbol, historical_data)
            
            # Log box analysis
            box_message = (
                f"Box Analysis - Symbol: {symbol}\n"
                f"Box Detected: {analysis.get('box_detected', False)}\n"
                f"Box Top: ${analysis.get('box_top', 0.00):.2f}\n"
                f"Box Bottom: ${analysis.get('box_bottom', 0.00):.2f}\n"
                f"Breakout Direction: {analysis.get('breakout_direction', 'None')}\n"
                f"Volume Confirmation: {analysis.get('volume_confirmation', False)}"
            )
            self.loggers['box_method'].info(box_message)
            self.discord_webhook.stream_logs('box_method', box_message)
            
            if analysis.get('box_detected'):
                await self._process_box_breakout(symbol, analysis)
                
        except Exception as e:
            self.loggers['errors'].error(f"Error handling price update: {str(e)}")

    def _process_box_breakout(self, symbol: str, analysis: Dict[str, Any]):
        """Process a box breakout signal"""
        try:
            # Check if we already have an active trade
            if symbol in self.active_trades:
                return
                
            # Check if we've reached max concurrent trades
            if len(self.active_trades) >= self.technical_analyzer.box_analyzer.max_concurrent_trades:
                return
            
            # Get sentiment analysis
            sentiment = self.sentiment_analyzer.analyze(symbol)
            
            # Generate AI explanation
            explanation = self.ai_explainer.explain_signal(
                symbol=symbol,
                price=analysis['current_price'],
                technical_analysis=analysis,
                sentiment_analysis=sentiment
            )
            
            # Log trade signal
            self.loggers['trades'].info(
                f"New Trade Signal - Symbol: {symbol}\n" +
                f"Type: {'CALL' if analysis['is_breakout_up'] else 'PUT'}\n" +
                f"Entry: ${analysis['breakout_price']:.2f}\n" +
                f"Stop Loss: ${analysis['stop_loss']:.2f}\n" +
                f"Box Range: ${analysis['box_top']:.2f} - ${analysis['box_bottom']:.2f}\n" +
                f"Sentiment Score: {sentiment:.2f}\n" +
                f"Explanation: {explanation}"
            )
            
            # Create trade signal
            signal = {
                'symbol': symbol,
                'option_type': 'call' if analysis['is_breakout_up'] else 'put',
                'entry_price': analysis['breakout_price'],
                'stop_loss': analysis['stop_loss'],
                'take_profits': analysis['take_profits'],
                'position_size': analysis['position_size'],
                'risk_amount': analysis['risk_amount'],
                'premium': analysis['premium'],
                'box_top': analysis['box_top'],
                'box_bottom': analysis['box_bottom'],
                'explanation': explanation
            }
            
            # Send to Discord
            self.discord_webhook.send_signal(signal)
            
            # Track active trade
            self.active_trades[symbol] = {
                'entry_time': datetime.now(),
                'signal': signal
            }
            
        except Exception as e:
            self.loggers['errors'].error(f"Error processing box breakout: {str(e)}")

    async def _handle_news_update(self, event: Event):
        """Handle news update events"""
        try:
            symbol = event.data.get('symbol')
            news = event.data.get('news')
            
            if not all([symbol, news]):
                return
                
            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze(news)
            
            # Publish sentiment update
            await self.event_queue.publish(Event(
                event_type="sentiment_update",
                priority=EventPriority.MEDIUM,
                data={
                    'symbol': symbol,
                    'sentiment': sentiment
                }
            ))
                
        except Exception as e:
            self.logger.error(f"Error handling news update: {str(e)}")

    def _handle_sentiment_update(self, event: Event):
        """Handle sentiment update events"""
        try:
            symbol = event.data.get('symbol')
            sentiment = event.data.get('sentiment')
            
            if not all([symbol, sentiment]):
                return
                
            # Check if we have an active trade
            if symbol in self.active_trades:
                trade = self.active_trades[symbol]
                
                # Check if sentiment has changed significantly
                if abs(sentiment - trade['signal'].get('sentiment', 0)) > 0.2:
                    # Update trade with new sentiment
                    trade['signal']['sentiment'] = sentiment
                    
                    # Send update to Discord
                    self.discord_webhook.send_update({
                        'symbol': symbol,
                        'type': 'sentiment_update',
                        'new_sentiment': sentiment,
                        'explanation': f"Significant sentiment change detected for {symbol}"
                    })
            
        except Exception as e:
            self.logger.error(f"Error handling sentiment update: {str(e)}")

    def _is_market_open(self) -> bool:
        """Check if market is open"""
        return self.alpaca.is_market_open()

    async def _check_market_events(self):
        """Check for market events"""
        for symbol in TRADING_SYMBOLS:
            try:
                # Get latest price and volume
                price_data = self.alpaca.get_latest_quote(symbol)
                
                if price_data:
                    # Create price update event
                    price_event = Event(
                        event_type="price_update",
                        priority=EventPriority.HIGH,
                        data={
                            'symbol': symbol,
                            'price': price_data['ask_price'],
                            'volume': price_data['ask_size']
                        },
                        timestamp=datetime.now(),
                        source="market_monitor"
                    )
                    
                    # Publish price update
                    await self.event_queue.publish(price_event)
                    
            except Exception as e:
                self.logger.error(f"Error checking market events for {symbol}: {str(e)}")
                
        # Wait a bit before next check
        await asyncio.sleep(1)  # Check every second

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get OpenAI API key from environment
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    agent = TradingAgent()
    agent.start() 