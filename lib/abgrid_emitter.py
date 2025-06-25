"""
Event-driven logging system for AB-Grid project operations.

This module provides a decorator-based notification system using event emitters
and listeners to track function execution with structured logging capabilities.

Author: Pierpaolo Calanna
Date Created: May 3, 2025
License: MIT License
"""

from typing import Any, Dict, List, Protocol, TypedDict, Union, runtime_checkable
from collections import defaultdict

class Base(TypedDict):
    """Base event data structure."""
    event_type: str

class RegularEventData(Base):
    """Extended event data for regular events."""
    event_message: str

class TracebackErrorEventData(Base):
    """Event data for errors with traceback information."""
    event_message: List[Dict[str, Any]]  # Override to accept traceback list
    exception_type: str
    exception_str: str

# Union type for all possible event data structures
EventData = Union[RegularEventData, TracebackErrorEventData]

@runtime_checkable
class EventListener(Protocol):
    """Protocol for objects that can handle emitted events."""
    
    def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Process an emitted event.
        
        Args:
            event_type: Event identifier (e.g., 'operation_start', 'operation_error')
            data: Event payload containing operation_name, operation_value, and other relevant information
        """
        ...

class EventEmitter:
    """
    Event emitter managing listeners and broadcasting events.
    Supports multiple listeners per event type with automatic cleanup
    and error-safe event emission.
    """
    
    def __init__(self) -> None:
        """Initialize with empty listener registry."""
        # Init listeners
        self._listeners: Dict[str, List[EventListener]] = defaultdict(list)
    
    def add_listener(self, event_type: str, listener: EventListener) -> None:
        """
        Register a listener for specific event types.
        
        Args:
            event_type: Event type to subscribe to
            listener: Object implementing EventListener protocol
            
        Raises:
            TypeError: If listener doesn't implement EventListener protocol
        """
        if not isinstance(listener, EventListener):
            raise TypeError(f"Listener must implement EventListener protocol, got {type(listener)}")
        self._listeners[event_type].append(listener)
    
    def remove_listener(self, event_type: str, listener: EventListener) -> None:
        """
        Unregister a listener from an event type.
        
        Args:
            event_type: Event type to unsubscribe from
            listener: Listener object to remove
            
        Note:
            Silently ignores if listener is not found.
        """
        try:
            self._listeners[event_type].remove(listener)
        except (KeyError, ValueError):
            pass  # Event type doesn't exist or listener not found
    
    def emit(self, data: EventData) -> None:
        """
        Broadcast event to all registered listeners.
        
        Args:
            data: Event data conforming to EventData type
            
        Note:
            Continues emission even if individual listeners fail.
        """
        event_type = data["event_type"]
        for listener in self._listeners[event_type]:
            try:
                listener.handle_event(data)
            except Exception as e:
                # Log listener errors but don't stop other listeners
                print(f"Warning: Listener {type(listener).__name__} failed to handle {event_type}: {e}")
