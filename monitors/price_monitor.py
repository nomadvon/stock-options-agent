import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockQuotesRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data import StockHistoricalDataClient
from events.event_queue import EventQueue

logger = logging.getLogger(__name__)

class PriceMonitor:
    """Monitors price changes and publishes events"""
    
    def __init__(self, api_key: str, api_secret: str, event_queue: EventQueue):
        self.api_key = api_key
        self.api_secret = api_secret
        self.event_queue = event_queue
        self.stream = None
        self.hist_client = None
        self.last_prices: Dict[str, float] = {}
        self.running = False
        self._stream_task = None
        
    async def start(self, symbols: list[str]):
        """Start monitoring prices for given symbols"""
        try:
            self.running = True
            logger.info(f"Starting price monitor for symbols: {symbols}")
            
            # Initialize clients
            self.stream = StockDataStream(self.api_key, self.api_secret)
            self.hist_client = StockHistoricalDataClient(self.api_key, self.api_secret)
            logger.info("Initialized Alpaca clients")
            
            # Get initial prices
            await self._get_initial_prices(symbols)
            logger.info(f"Got initial prices: {self.last_prices}")
            
            # Subscribe to price updates
            self.stream.subscribe_quotes(self._handle_price_update, *symbols)
            logger.info(f"Subscribed to price updates for {symbols}")
            
            # Start the stream in a separate task
            self._stream_task = asyncio.create_task(self._run_stream())
            logger.info("Started price stream task")
            
        except Exception as e:
            logger.error(f"Error starting price monitor: {e}")
            self.running = False
            raise
        
    async def stop(self):
        """Stop monitoring prices"""
        logger.info("Stopping price monitor...")
        self.running = False
        if self.stream:
            try:
                if self._stream_task:
                    logger.info("Stopping price stream...")
                    self.stream.stop()
                    try:
                        await asyncio.wait_for(self._stream_task, timeout=5.0)
                        logger.info("Price stream stopped successfully")
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for stream task to complete")
                    except Exception as e:
                        logger.error(f"Error waiting for stream task: {e}")
            except Exception as e:
                logger.error(f"Error stopping stream: {e}")
        logger.info("Price monitor stopped")
        
    async def _run_stream(self):
        """Run the stream in a separate task"""
        try:
            logger.info("Starting price stream...")
            while self.running:
                try:
                    if self.stream:
                        # Run the stream in a separate task to avoid blocking
                        logger.info("Connecting to Alpaca websocket stream...")
                        stream_task = asyncio.create_task(self.stream.run())
                        try:
                            await stream_task
                            logger.info("Stream task completed")
                        except asyncio.CancelledError:
                            logger.info("Stream task cancelled")
                            break
                        except Exception as e:
                            logger.error(f"Error in stream task: {e}")
                            if self.running:
                                logger.info("Retrying stream in 5 seconds...")
                                await asyncio.sleep(5)  # Wait before retrying
                                continue
                    else:
                        logger.error("Stream is None, stopping")
                        self.running = False
                        break
                except Exception as e:
                    logger.error(f"Error in stream: {e}")
                    if self.running:
                        logger.info("Retrying stream in 5 seconds...")
                        await asyncio.sleep(5)  # Wait before retrying
                        continue
        except Exception as e:
            logger.error(f"Fatal error in stream: {e}")
            self.running = False
        
    async def _get_initial_prices(self, symbols: list[str]):
        """Get initial prices for symbols"""
        try:
            # Get the latest quote for each symbol
            request = StockQuotesRequest(symbol_or_symbols=symbols)
            
            # Get the quotes from Alpaca
            quotes = self.hist_client.get_stock_latest_quote(request)
            
            # Store the last prices
            for symbol in symbols:
                if symbol in quotes:
                    quote = quotes[symbol]
                    if hasattr(quote, 'ask_price') and quote.ask_price:
                        self.last_prices[symbol] = float(quote.ask_price)
                    
        except Exception as e:
            logger.error(f"Error getting initial prices: {e}")
            
    async def _handle_price_update(self, quote):
        """Handle price updates from the stream"""
        try:
            symbol = quote.symbol
            current_price = float(quote.ask_price)
            volume = int(quote.ask_size)
            
            logger.info(f"Received price update for {symbol}: ${current_price:.2f} (Volume: {volume:,})")
            
            # Calculate price change
            if symbol in self.last_prices:
                last_price = self.last_prices[symbol]
                price_change = (current_price - last_price) / last_price
                
                logger.info(f"Price change for {symbol}: {price_change:.2%}")
                
                # Publish price update event
                await self.event_queue.publish_price_update(
                    symbol=symbol,
                    price=current_price,
                    volume=volume,
                    change=price_change
                )
                logger.info(f"Published price update event for {symbol}")
                
            # Update last price
            self.last_prices[symbol] = current_price
            
        except Exception as e:
            logger.error(f"Error handling price update: {e}") 