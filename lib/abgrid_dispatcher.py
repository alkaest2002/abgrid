"""
Event-driven system for AB-Grid project operations.

The system uses a publish-subscribe pattern where events are dispatched by operations
and handled by registered subscribers (such as loggers, metrics collectors, etc.).

Author: Pierpaolo Calanna
Date Created: Wed Jun 25 2025
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

@runtime_checkable
class Subscriber(Protocol):
    """
    Protocol defining the interface for event subscribers.
    
    Any class implementing this protocol can subscribe to specific event types
    and will receive notifications when those events are dispatched by the system.
    
    Examples:
        - Console loggers
        - File loggers  
        - Metrics collectors
        - Alert systems
    """
    
    def on_event(self, data: Dict[str, Any]) -> None:
        """
        Handle an event dispatched by the system.
        
        This method is called by the EventDispatcher when an event of the
        subscribed type is dispatched. Implementations should handle any
        processing errors gracefully to avoid disrupting other subscribers.
        
        Args:
            data (Dict[str, Any]): Complete event data dictionary containing:
                - event_type (str): Event identifier
                - event_message (str | List[Dict]): Event payload
                - Additional fields based on event type
                
        Returns:
            None
            
        Note:
            This method should not raise exceptions as it may prevent
            other subscribers from receiving events.
        """
        ...

class Dispatcher:
    """
    Central event broadcasting system managing subscribers and event distribution.
    
    This class implements the publisher side of the publish-subscribe pattern,
    maintaining a registry of subscribers and broadcasting events to appropriate
    subscribers. It supports multiple subscribers per event type and provides
    error isolation between subscribers.
    
    The dispatcher allows subscribers to register themselves for specific event types
    and then broadcasts events to all registered subscribers of the matching type.
    
    Attributes:
        _subscribers (Dict[str, List[Subscriber]]): Registry mapping event types
            to their corresponding subscriber lists.
    """
    
    def __init__(self) -> None:
        """
        Initialize the event dispatcher with an empty subscriber registry.
        
        Creates a defaultdict that automatically initializes empty lists
        for new event types, simplifying subscriber management.
        """
        # Registry of subscribers organized by event type
        # defaultdict ensures we don't need to check for key existence
        self._subscribers: Dict[str, List[Subscriber]] = defaultdict(list)
    
    def subscribe(self, event_type: str, subscriber: Subscriber) -> None:
        """
        Register a subscriber to receive events of a specific type.
        
        This method is typically called by subscribers themselves through their
        subscribe_to() method, but can also be called directly for manual registration.
        The subscriber will receive all future events of the specified type until removed.
        
        Args:
            event_type (str): Event type identifier to subscribe to
                (e.g., 'operation_start', 'operation_error', 'operation_end')
            subscriber (Subscriber): Object implementing the Subscriber protocol
                
        Raises:
            TypeError: If the provided subscriber doesn't implement the Subscriber protocol
            
        Note:
            The same subscriber can be registered for multiple event types,
            and multiple subscribers can be registered for the same event type.
        """
        if not isinstance(subscriber, Subscriber):
            raise TypeError(
                f"Subscriber must implement Subscriber protocol, "
                f"got {type(subscriber).__name__}"
            )
        
        # Add subscriber to the event type's subscriber list
        self._subscribers[event_type].append(subscriber)
    
    def unsubscribe(self, event_type: str, subscriber: Subscriber) -> None:
        """
        Unregister a subscriber from receiving events of a specific type.
        
        Removes the specified subscriber from the event type's subscriber list.
        This operation is idempotent - calling it multiple times has no effect.
        
        Args:
            event_type (str): Event type to unsubscribe from
            subscriber (Subscriber): Subscriber object to remove from registry
            
        Note:
            Silently ignores cases where:
            - The event type doesn't exist in the registry
            - The subscriber is not registered for the specified event type
        """
        try:
            self._subscribers[event_type].remove(subscriber)
        except (KeyError, ValueError):
            # KeyError: event_type doesn't exist in registry
            # ValueError: subscriber not found in the list
            pass  # Fail silently to make operation idempotent
    
    def dispatch(self, data: Union[RegularEventData, TracebackErrorEventData]) -> None:
        """
        Broadcast an event to all registered subscribers of the appropriate type.
        
        Iterates through all subscribers registered for the event type and
        calls their on_event method. If a subscriber raises an exception,
        it's caught and logged to the console, but dispatch continues to other subscribers.
        
        Args:
            data (EventData): Event data conforming to one of the defined
                event data structures (RegularEventData or TracebackErrorEventData).
                Must contain at minimum an 'event_type' field.
                
        Returns:
            None
            
        Note:
            Subscriber exceptions are caught and logged to prevent one failing
            subscriber from preventing others from receiving events. This ensures
            system robustness when dealing with multiple event handlers.
        """
        event_type: str = data["event_type"]
        
        # Get all subscribers for this event type
        subscribers = self._subscribers[event_type]
        
        # If no subscribers are registered, silently return
        if not subscribers:
            return
        
        # Iterate through all registered subscribers for this event type
        for subscriber in subscribers:
            try:
                # Delegate event handling to the subscriber
                subscriber.on_event(data)
            except Exception as e:
                # Log subscriber errors but continue with other subscribers
                # This ensures one faulty subscriber doesn't break the entire system
                print(
                    f"Warning: Subscriber {type(subscriber).__name__} failed to handle "
                    f"event '{event_type}': {e}"
                )
    
    def get_subscriber_count(self, event_type: Optional[str] = None) -> Union[int, Dict[str, int]]:
        """
        Get the number of registered subscribers for event type(s).
        
        This method is useful for debugging, monitoring, and system diagnostics
        to understand the current subscription state.
        
        Args:
            event_type (Optional[str]): Specific event type to query.
                If None, returns counts for all event types.
                
        Returns:
            Union[int, Dict[str, int]]: Either the count for a specific event type,
                or a dictionary mapping event types to their subscriber counts.
        """
        if event_type is not None:
            return len(self._subscribers[event_type])
        else:
            return {et: len(subscribers) for et, subscribers in self._subscribers.items()}
    
    def clear_subscribers(self, event_type: Optional[str] = None) -> None:
        """
        Remove all subscribers for specified event type(s).
        
        This method is useful for cleanup operations, testing scenarios,
        or when you need to reset the subscription state.
        
        Args:
            event_type (Optional[str]): Event type to clear subscribers for.
                If None, clears all subscribers for all event types.
                    
        Returns:
            None
        """
        if event_type is not None:
            self._subscribers[event_type].clear()
        else:
            self._subscribers.clear()
    
    def get_event_types(self) -> List[str]:
        """
        Get a list of all event types that have registered subscribers.
        
        Returns:
            List[str]: List of event type identifiers that have at least one subscriber.
        """
        return list(self._subscribers.keys())
    
    def has_subscribers(self, event_type: str) -> bool:
        """
        Check if a specific event type has any registered subscribers.
        
        Args:
            event_type (str): Event type to check for subscribers
            
        Returns:
            bool: True if the event type has at least one subscriber, False otherwise.
        """
        return len(self._subscribers[event_type]) > 0
    
    def get_subscribers(self, event_type: str) -> List[Subscriber]:
        """
        Get a copy of the subscriber list for a specific event type.
        
        Returns a copy to prevent external modification of the internal registry.
        
        Args:
            event_type (str): Event type to get subscribers for
            
        Returns:
            List[Subscriber]: Copy of the subscriber list for the specified event type.
                Returns an empty list if no subscribers are registered.
        """
        return self._subscribers[event_type].copy()