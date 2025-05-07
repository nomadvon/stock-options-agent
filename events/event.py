from enum import Enum
from typing import Dict, Any
from datetime import datetime

class EventPriority(Enum):
    """Priority levels for events"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class Event:
    """Event class for the event system"""
    
    def __init__(self, event_type: str, priority: EventPriority = EventPriority.MEDIUM, 
                 data: Dict[str, Any] = None, timestamp: datetime = None, source: str = None):
        """
        Initialize an event
        
        Args:
            event_type: Type of event (e.g., 'price_update', 'news_update')
            priority: Priority level of the event
            data: Event data dictionary
            timestamp: Event timestamp (defaults to current time)
            source: Source of the event
        """
        self.event_type = event_type
        self.priority = priority
        self.data = data or {}
        self.timestamp = timestamp or datetime.now()
        self.source = source
        
    def __lt__(self, other):
        """Less than comparison for priority queue ordering"""
        if not isinstance(other, Event):
            return NotImplemented
        # Compare by priority first, then timestamp
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp
        
    def __eq__(self, other):
        """Equality comparison"""
        if not isinstance(other, Event):
            return NotImplemented
        return (self.priority.value == other.priority.value and 
                self.timestamp == other.timestamp)
        
    def __str__(self) -> str:
        """String representation of the event"""
        return f"Event(type={self.event_type}, priority={self.priority.name}, data={self.data})"
        
    def __repr__(self) -> str:
        """Detailed string representation of the event"""
        return (f"Event(event_type='{self.event_type}', "
                f"priority=EventPriority.{self.priority.name}, "
                f"data={self.data}, "
                f"timestamp={self.timestamp}, "
                f"source='{self.source}')") 