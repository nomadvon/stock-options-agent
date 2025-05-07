import logging
import os
import sys
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

from trading_agent import TradingAgent
from events.event_queue import EventQueue
from monitors.price_monitor import PriceMonitor
from monitors.news_monitor import NewsMonitor
from processors.event_processor import EventProcessor
from generators.signal_generator import SignalGenerator
from data.alpaca_connector import AlpacaConnector
from config.config import (
    TRADING_SYMBOLS,
    MARKET_HOURS,
    CHECK_INTERVAL_MINUTES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def is_market_open() -> bool:
    """Check if the market is currently open using Alpaca's API"""
    try:
        alpaca = AlpacaConnector()
        is_open = alpaca.is_market_open()
        logger.info(f"Market status from Alpaca: {'Open' if is_open else 'Closed'}")
        return is_open
    except Exception as e:
        logger.error(f"Error checking market status: {e}")
        return False

async def run_production():
    """Run the trading agent in production mode"""
    try:
        # Initialize components
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        # Initialize event system
        event_queue = EventQueue()
        logger.info("Initialized event queue")
        
        # Initialize monitors
        price_monitor = PriceMonitor(
            api_key=os.getenv('ALPACA_API_KEY'),
            api_secret=os.getenv('ALPACA_API_SECRET'),
            event_queue=event_queue
        )
        logger.info("Initialized price monitor")
        
        news_monitor = NewsMonitor(event_queue)
        logger.info("Initialized news monitor")
        
        # Initialize processors
        event_processor = EventProcessor(event_queue)
        logger.info("Initialized event processor")
        
        signal_generator = SignalGenerator(event_queue, openai_api_key)
        logger.info("Initialized signal generator")
        
        # Initialize trading agent (this will send the production deployment message)
        agent = TradingAgent(event_queue)
        logger.info("Initialized trading agent")
        
        logger.info("Starting production deployment...")
        
        # Start the agent first to send Discord message
        await agent.start()
        logger.info("Trading agent started")
        
        # Start news monitoring immediately (24/7)
        await event_queue.start()
        logger.info("Event queue started")
        
        await news_monitor.start(TRADING_SYMBOLS)
        logger.info("News monitor started")
        
        await event_processor.start()
        logger.info("Event processor started")
        
        logger.info("Entering main loop...")
        while True:
            try:
                # Check if market is open
                logger.info("Checking market status...")
                market_status = is_market_open()
                logger.info(f"Market status: {'Open' if market_status else 'Closed'}")
                
                if market_status:
                    logger.info("Market is open - starting price monitoring...")
                    
                    # Start price monitoring only during market hours
                    logger.info("Starting price monitor...")
                    await price_monitor.start(TRADING_SYMBOLS)
                    logger.info("Price monitor started")
                    
                    logger.info("Starting signal generator...")
                    await signal_generator.start()
                    logger.info("Signal generator started")
                    
                    # Keep running until market closes
                    logger.info("Entering market hours loop...")
                    while is_market_open():
                        await asyncio.sleep(1)
                    
                    # Stop only price-related components when market closes
                    logger.info("Market closed - stopping price-related components...")
                    await signal_generator.stop()
                    await price_monitor.stop()
                    logger.info("Price-related components stopped")
                    
                else:
                    # Get next market open time from Alpaca
                    logger.info("Getting next market open time...")
                    alpaca = AlpacaConnector()
                    market_hours = alpaca.get_market_hours()
                    
                    if market_hours:
                        next_open = market_hours['open']
                        # Convert current time to UTC to match Alpaca's timezone
                        current_time = datetime.now(pytz.UTC)
                        wait_time = (next_open - current_time).total_seconds()
                        logger.info(f"Market is closed. Waiting {wait_time/3600:.1f} hours until market opens at {next_open.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        
                        # Send Discord message about market hours sleep
                        agent.discord_webhook.send_update({
                            'type': 'market_hours',
                            'message': f"Market is closed. Waiting {wait_time/3600:.1f} hours until market opens at {next_open.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                        })
                        
                        # Sleep until market opens
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error("Could not get market hours from Alpaca")
                        await asyncio.sleep(60)  # Wait a minute before retrying
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                # Send Discord message about error
                agent.discord_webhook.send_update({
                    'type': 'error',
                    'message': f"Error in main loop: {str(e)}"
                })
                await asyncio.sleep(60)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"Fatal error in production deployment: {e}")
        # Send Discord message about fatal error
        agent.discord_webhook.send_update({
            'type': 'fatal_error',
            'message': f"Fatal error in production deployment: {str(e)}"
        })
    finally:
        # Ensure clean shutdown of all components
        try:
            await news_monitor.stop()
            await event_processor.stop()
            await event_queue.stop()
            logger.info("All components stopped")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    # Run the production script
    asyncio.run(run_production()) 