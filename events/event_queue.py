import asyncio
import logging
from typing import Dict, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from functools import total_ordering
from events.event import Event, EventPriority

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Event:
    event_type: str
    data: Dict[str, Any]
    priority: EventPriority
    timestamp: datetime
    source: str

    def __lt__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        # Compare only by priority first, then timestamp
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp

    def __eq__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        return (self.priority.value == other.priority.value and 
                self.timestamp == other.timestamp)

class EventQueue:
    """Manages event flow and processing"""
    
    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self.handlers: Dict[str, list[Callable]] = {}
        self.running = False
        self.processing_tasks = set()
        
    async def start(self):
        """Start the event queue processing"""
        logger.info("Starting event queue...")
        self.running = True
        asyncio.create_task(self._process_events())
        logger.info("Event queue started")
        
    async def stop(self):
        """Stop the event queue processing"""
        logger.info("Stopping event queue...")
        self.running = False
        await asyncio.gather(*self.processing_tasks)
        logger.info("Event queue stopped")
        
    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for a specific event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
        
    async def publish(self, event: Event):
        """Publish an event to the queue"""
        logger.info(f"Publishing event: {event.event_type} from {event.source}")
        await self.queue.put(event)
        logger.info(f"Event published: {event.event_type}")
        
    async def _process_events(self):
        """Process events from the queue"""
        logger.info("Starting event processing loop")
        while self.running:
            try:
                event = await self.queue.get()
                logger.info(f"Processing event: {event.event_type} from {event.source}")
                
                if event.event_type in self.handlers:
                    for handler in self.handlers[event.event_type]:
                        logger.info(f"Executing handler for event: {event.event_type}")
                        task = asyncio.create_task(self._execute_handler(handler, event))
                        self.processing_tasks.add(task)
                        task.add_done_callback(self.processing_tasks.discard)
                else:
                    logger.warning(f"No handlers registered for event type: {event.event_type}")
                    
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    async def _execute_handler(self, handler: Callable, event: Event):
        """Execute a handler for an event"""
        try:
            logger.info(f"Executing handler for event: {event.event_type}")
            await handler(event)
            logger.info(f"Handler completed for event: {event.event_type}")
        except Exception as e:
            logger.error(f"Error in event handler: {e}")
            
    async def publish_price_update(self, symbol: str, price: float, volume: int, change: float):
        """Helper method to publish price updates"""
        priority = EventPriority.HIGH if abs(change) > 0.02 else EventPriority.MEDIUM
        event = Event(
            event_type="price_update",
            data={
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "change": change
            },
            priority=priority,
            timestamp=datetime.now(),
            source="price_monitor"
        )
        logger.info(f"Publishing price update for {symbol}: ${price:.2f} (Change: {change:.2%})")
        await self.publish(event)
        
    async def publish_news_update(self, symbol: str, article: Dict[str, Any]):
        """Helper method to publish news updates"""
        event = Event(
            event_type="news_update",
            data={"symbol": symbol, "article": article},
            priority=EventPriority.MEDIUM,
            timestamp=datetime.now(),
            source="news_monitor"
        )
        logger.info(f"Publishing news update for {symbol}")
        await self.publish(event) 