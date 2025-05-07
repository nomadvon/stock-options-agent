import logging
import asyncio
from datetime import datetime, timedelta
from trading_agent import TradingAgent
from alerts.discord_webhook import DiscordWebhook
from config.config import TAKE_PROFIT_LEVELS, STOP_LOSS_LEVELS
from events.event_queue import EventQueue, Event, EventPriority
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_premium_thresholds(agent: TradingAgent):
    """Test the premium calculation with various price points"""
    print("\nTesting Premium Thresholds:")
    print("=" * 50)
    
    test_cases = [
        ("SPY", 500.0),  # High price
        ("SPY", 100.0),  # Medium price
        ("SPY", 50.0),   # Low price
    ]
    
    for symbol, price in test_cases:
        # Test both call and put options
        for option_type in ['call', 'put']:
            premium = agent._calculate_option_premium(
                symbol,
                price,
                option_type,
                agent._get_next_friday()
            )
            print(f"Symbol: {symbol}, Price: ${price:.2f}, Type: {option_type.upper()}")
            print(f"Calculated Premium: ${premium:.2f}")
            print("-" * 30)

async def test_event_driven_system():
    """Test the event-driven trading system"""
    # Get OpenAI API key from environment
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Initialize event queue and agent
    event_queue = EventQueue()
    agent = TradingAgent(openai_api_key, event_queue)
    
    # Test premium thresholds first
    test_premium_thresholds(agent)
    
    print("\nTesting event-driven trading system...")
    print("=" * 50)
    
    # Start the agent
    await agent.start()
    
    # Create test events
    current_time = datetime.now()
    test_events = [
        Event(
            event_type="price_update",
            data={
            "symbol": "SPY",
                "price": 500.0,
                "timestamp": current_time.isoformat()
            },
            priority=EventPriority.HIGH,
            timestamp=current_time,
            source="test_price_monitor"
        ),
        Event(
            event_type="news_update",
            data={
                "symbol": "SPY",
                "sentiment": {
                    "overall_score": 0.8,
                    "sentiment_label": "positive",
                    "article_count": 5
                },
                "timestamp": current_time.isoformat()
            },
            priority=EventPriority.MEDIUM,
            timestamp=current_time,
            source="test_news_monitor"
        )
    ]
    
    # Add events to queue
    for event in test_events:
        await event_queue.publish(event)
        print(f"Added {event.event_type} event to queue")
    
    # Wait for events to be processed
    print("\nWaiting for events to be processed...")
    await asyncio.sleep(2)
    
    # Stop the agent
    await agent.stop()
    print("\nTest completed.")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_event_driven_system()) 