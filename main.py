import asyncio
import logging
import os
from typing import List
from dotenv import load_dotenv

from events.event_queue import EventQueue
from monitors.price_monitor import PriceMonitor
from monitors.news_monitor import NewsMonitor
from processors.event_processor import EventProcessor
from generators.signal_generator import SignalGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()  # Load environment variables from .env file

# Debug log environment variables (masking sensitive values)
logger.info("Environment variables loaded:")
logger.info(f"ALPACA_API_KEY: {'*' * len(os.getenv('ALPACA_API_KEY', ''))}")
logger.info(f"ALPACA_API_SECRET: {'*' * len(os.getenv('ALPACA_API_SECRET', ''))}")
logger.info(f"OPENAI_API_KEY: {'*' * len(os.getenv('OPENAI_API_KEY', ''))}")
logger.info(f"DISCORD_WEBHOOK_URL: {'*' * len(os.getenv('DISCORD_WEBHOOK_URL', ''))}")
logger.info(f"NEWS_API_KEY: {'*' * len(os.getenv('NEWS_API_KEY', ''))}")
logger.info(f"AWS_ACCESS_KEY_ID: {'*' * len(os.getenv('AWS_ACCESS_KEY_ID', ''))}")
logger.info(f"AWS_SECRET_ACCESS_KEY: {'*' * len(os.getenv('AWS_SECRET_ACCESS_KEY', ''))}")
logger.info(f"AWS_REGION: {os.getenv('AWS_REGION', 'not set')}")

# Configuration
TRADING_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL']

async def main():
    """Initialize and run the trading system"""
    try:
        # Initialize components
        event_queue = EventQueue()
        price_monitor = PriceMonitor(
            api_key=os.getenv('ALPACA_API_KEY'),
            api_secret=os.getenv('ALPACA_API_SECRET'),
            event_queue=event_queue
        )
        news_monitor = NewsMonitor(event_queue)
        event_processor = EventProcessor(event_queue)
        signal_generator = SignalGenerator(
            event_queue=event_queue,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Start components in order
        await event_queue.start()
        await price_monitor.start(TRADING_SYMBOLS)
        await news_monitor.start(TRADING_SYMBOLS)  # Pass symbols to news monitor
        await event_processor.start()
        await signal_generator.start()
        
        # Keep the main loop running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Cleanup
        await event_queue.stop()
        await price_monitor.stop()
        await news_monitor.stop()
        await event_processor.stop()
        await signal_generator.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
