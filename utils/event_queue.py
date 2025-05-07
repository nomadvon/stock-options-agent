import logging
from typing import Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class EventPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass
class Event:
    event_type: str
    priority: EventPriority
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class EventQueue:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = True
        
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"Subscribed to {event_type}")
        
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)
            self.logger.debug(f"Unsubscribed from {event_type}")
            
    def publish(self, event: Event):
        """Publish an event to subscribers"""
        if not self.running:
            return
            
        event_type = event.event_type
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_type}: {str(e)}")
                    
    def stop(self):
        """Stop the event queue"""
        self.running = False
        self.logger.info("Event queue stopped") 