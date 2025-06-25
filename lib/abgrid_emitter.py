"""
Event-driven system for AB-Grid project operations.

The system uses a publish-subscribe pattern where events are emitted by operations
and handled by registered listeners (such as loggers, metrics collectors, etc.).

Author: Pierpaolo Calanna
Date Created: May 3, 2025
License: MIT License
"""

from typing import Any, Dict, List, Protocol, TypedDict, Union, runtime_checkable, Optional
from collections import defaultdict


class Base(TypedDict):
    """
    Base event data structure containing common fields for all events.
    
    This serves as the foundation for all event types in the system,
    ensuring every event has at minimum an event type identifier.
    """
    event_type: str


class RegularEventData(Base):
    """
    Event data structure for standard operation events.
    
    Used for typical operation lifecycle events like start, progress,
    completion, etc. where the message is a simple string.
    """
    event_message: str


class TracebackErrorEventData(Base):
    """
    Event data structure for error events with detailed traceback information.
    
    Contains comprehensive error details including exception information
    and a structured traceback for debugging purposes.
    """
    event_message: List[Dict[str, Any]]  # List of traceback frame dictionaries
    exception_type: str                  # Exception class name (e.g., 'ValueError')
    exception_str: str                   # String representation of the exception


# Union type encompassing all possible event data structures
EventData = Union[RegularEventData, TracebackErrorEventData]


@runtime_checkable
class EventListener(Protocol):
    """
    Protocol defining the interface for event listeners.
    
    Any class implementing this protocol can be registered as an event listener
    to receive and process events emitted by the system.
    
    Examples:
        - Console loggers
        - File loggers  
        - Metrics collectors
        - Alert systems
    """
    
    def handle_event(self, data: Dict[str, Any]) -> None:
        """
        Process an emitted event with its associated data.
        
        This method is called by the EventEmitter when an event of the
        subscribed type is emitted. Implementations should handle any
        processing errors gracefully to avoid disrupting other listeners.
        
        Args:
            data (Dict[str, Any]): Complete event data dictionary containing:
                - event_type (str): Event identifier
                - event_message (str | List[Dict]): Event payload
                - Additional fields based on event type
                
        Returns:
            None
            
        Note:
            This method should not raise exceptions as it may prevent
            other listeners from receiving events.
        """
        ...


class EventEmitter:
    """
    Central event broadcasting system managing listeners and event distribution.
    
    This class implements the publisher side of the publish-subscribe pattern,
    maintaining a registry of listeners and broadcasting events to appropriate
    subscribers. It supports multiple listeners per event type and provides
    error isolation between listeners.
    
    Attributes:
        _listeners (Dict[str, List[EventListener]]): Registry mapping event types
            to their corresponding listener lists.
            
    Examples:
        >>> emitter = EventEmitter()
        >>> logger = ConsoleLogger()
        >>> emitter.add_listener('error', logger)
        >>> emitter.emit({'event_type': 'error', 'event_message': 'Something failed'})
    """
    
    def __init__(self) -> None:
        """
        Initialize the event emitter with an empty listener registry.
        
        Creates a defaultdict that automatically initializes empty lists
        for new event types, simplifying listener management.
        """
        # Registry of listeners organized by event type
        # defaultdict ensures we don't need to check for key existence
        self._listeners: Dict[str, List[EventListener]] = defaultdict(list)
    
    def add_listener(self, event_type: str, listener: EventListener) -> None:
        """
        Register a listener to receive events of a specific type.
        
        The listener will be added to the registry and will receive all
        future events of the specified type until removed.
        
        Args:
            event_type (str): Event type identifier to subscribe to
                (e.g., 'operation_start', 'operation_error', 'operation_end')
            listener (EventListener): Object implementing the EventListener protocol
                
        Raises:
            TypeError: If the provided listener doesn't implement the EventListener protocol
            
        Note:
            The same listener can be registered for multiple event types,
            and multiple listeners can be registered for the same event type.
        """
        if not isinstance(listener, EventListener):
            raise TypeError(
                f"Listener must implement EventListener protocol, "
                f"got {type(listener).__name__}"
            )
        
        # Add listener to the event type's subscriber list
        self._listeners[event_type].append(listener)
    
    def remove_listener(self, event_type: str, listener: EventListener) -> None:
        """
        Unregister a listener from receiving events of a specific type.
        
        Removes the specified listener from the event type's subscriber list.
        This operation is idempotent - calling it multiple times has no effect.
        
        Args:
            event_type (str): Event type to unsubscribe from
            listener (EventListener): Listener object to remove from registry
            
        Note:
            Silently ignores cases where:
            - The event type doesn't exist in the registry
            - The listener is not registered for the specified event type
        """
        try:
            self._listeners[event_type].remove(listener)
        except (KeyError, ValueError):
            # KeyError: event_type doesn't exist in registry
            # ValueError: listener not found in the list
            pass  # Fail silently to make operation idempotent
    
    def emit(self, data: EventData) -> None:
        """
        Broadcast an event to all registered listeners of the appropriate type.
        
        Iterates through all listeners registered for the event type and
        calls their handle_event method. If a listener raises an exception,
        it's caught and logged, but emission continues to other listeners.
        
        Args:
            data (EventData): Event data conforming to one of the defined
                event data structures (RegularEventData or TracebackErrorEventData)
                
        Returns:
            None
            
        Note:
            Listener exceptions are caught and logged to prevent one failing
            listener from preventing others from receiving events. This ensures
            system robustness when dealing with multiple event handlers.
        """
        event_type: str = data["event_type"]
        
        # Iterate through all registered listeners for this event type
        for listener in self._listeners[event_type]:
            try:
                # Delegate event handling to the listener
                listener.handle_event(data)
            except Exception as e:
                # Log listener errors but continue with other listeners
                # This ensures one faulty listener doesn't break the entire system
                print(
                    f"Warning: Listener {type(listener).__name__} failed to handle "
                    f"event '{event_type}': {e}"
                )
    
    def get_listener_count(self, event_type: Optional[str] = None) -> Union[int, Dict[str, int]]:
        """
        Get the number of registered listeners for event type(s).
        
        Args:
            event_type (Optional[str]): Specific event type to query.
                If None, returns counts for all event types.
                
        Returns:
            Union[int, Dict[str, int]]: Either the count for a specific event type,
                or a dictionary mapping event types to their listener counts.
        """
        if event_type is not None:
            return len(self._listeners[event_type])
        else:
            return {et: len(listeners) for et, listeners in self._listeners.items()}
    
    def clear_listeners(self, event_type: Optional[str] = None) -> None:
        """
        Remove all listeners for specified event type(s).
        
        Args:
            event_type (Optional[str]): Event type to clear listeners for.
                If None, clears all listeners for all event types.
                
        Returns:
            None
        """
        if event_type is not None:
            self._listeners[event_type].clear()
        else:
            self._listeners.clear()
