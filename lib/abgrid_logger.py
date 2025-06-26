"""
Event-driven logging system for AB-Grid project operations.

This module provides a logger that subscribes to event dispatchers to track 
function execution with structured logging capabilities.

Author: Pierpaolo Calanna
Date Created: Wed Jun 25 2025
License: MIT License
"""
import textwrap
from typing import Any, Dict, List, Union
from lib import EVENT_ERROR


class Logger:
    """
    Console logger implementing EventSubscriber protocol.
    
    This class subscribes to operation lifecycle events and prints formatted messages
    to the console, including detailed error information with traceback data
    when errors occur.
    
    The logger distinguishes between regular operation events and error events,
    providing appropriate formatting for each type. It can subscribe to multiple
    event types across multiple dispatchers and manage its own subscriptions.
    
    Attributes:
        _subscriptions (Dict): Internal tracking of active subscriptions for cleanup purposes.
    
    Examples:
        >>> logger = PrintLogger()
        >>> logger.subscribe_to(dispatcher, 'start', 'end', 'error')
        >>> # Logger will now receive and display events when dispatcher dispatches them
        >>> logger.unsubscribe_from(dispatcher, 'start')  # Stop receiving start events
        >>> logger.unsubscribe_all()  # Clean up all subscriptions
    """
    
    def __init__(self, max_width: int = 80) -> None:
        """
        Initialize the print logger with empty subscription tracking.
        
        Sets up internal structures for managing subscriptions across
        multiple dispatchers and event types.
        
        Args:
            max_width (int): Maximum line width for text wrapping. Defaults to 80.
        """
        # Track active subscriptions for cleanup: {dispatcher: set of event_types}
        self._subscriptions: Dict[Any, set] = {}
        self._max_width: int = max_width
    
    def _pretty_print(self, text: str, prefix: str = "", width: int = None) -> None:
        """
         Print text with proper line wrapping and consistent prefix indentation.
        
        Handles text wrapping to ensure lines don't exceed specified width while
        maintaining proper indentation alignment for continuation lines. Gracefully
        handles edge cases including empty text, very long prefixes, and whitespace-only content.
        
        Args:
            text: The text content to print with wrapping applied.
            prefix: Optional prefix string for the first line (e.g., "Error: ", "Info: ").
            width: Maximum line width constraint. Uses instance default if None.
            
        Note:
            Continuation lines are automatically indented to align with the text portion
            of the first line. Ensures minimum width of 1 character even with long prefixes.
            Handles whitespace-only text and empty content gracefully.
        """
        width = width if width else self._max_width
            
        # Handle empty text
        if not text:
            return
        
        # Print text directly, if it fits on one line
        if len(full_line := f"{prefix}{text}") <= width:
            print(full_line)
            return
        
        # Text needs wrapping
        [first_line, *rest_of_lines] = textwrap.wrap(
            text,
            width=max(1, width - len(prefix)),
            break_long_words=True,
            break_on_hyphens=True
        )
        
        # Print first line with prefix
        print(f"{prefix}{first_line}")
        
        # Print rest of lines with indentation
        for line in rest_of_lines:
            print(f"{' ' * len(prefix)}{line}")
    
    def subscribe_to(self, dispatcher, *event_types: str) -> None:
        """
        Subscribe this logger to specific event types on a dispatcher.
        
        This method registers the logger with the dispatcher to receive notifications
        when events of the specified types are dispatched. The logger will start
        receiving and displaying these events immediately.
        
        Args:
            dispatcher: EventDispatcher instance to subscribe to. Must have a
                       subscribe() method that accepts event_type and subscriber.
            *event_types (str): Variable number of event type names to subscribe to.
                               Common types include 'start', 'end', 'error'.
                
        Returns:
            None
            
        Raises:
            AttributeError: If the dispatcher doesn't have a subscribe() method.
            TypeError: If the dispatcher rejects this logger (not implementing EventSubscriber).
        """
        # Track subscriptions for this dispatcher
        if dispatcher not in self._subscriptions:
            self._subscriptions[dispatcher] = set()
        
        for event_type in event_types:
            # Register with the dispatcher
            dispatcher.subscribe(event_type, self)
            
            # Track the subscription internally
            self._subscriptions[dispatcher].add(event_type)
    
    def unsubscribe_from(self, dispatcher, *event_types: str) -> None:
        """
        Unsubscribe this logger from specific event types on a dispatcher.
        
        Removes the logger's registration for the specified event types.
        The logger will stop receiving these events immediately.
        
        Args:
            dispatcher: EventDispatcher instance to unsubscribe from
            *event_types (str): Variable number of event type names to unsubscribe from
                
        Returns:
            None
            
        Note:
            This operation is idempotent - it won't fail if the logger wasn't
            subscribed to the specified event types.
        """
        if dispatcher not in self._subscriptions:
            return
        
        for event_type in event_types:
            # Unregister from the dispatcher
            dispatcher.unsubscribe(event_type, self)
            
            # Remove from internal tracking
            self._subscriptions[dispatcher].discard(event_type)
        
        # Clean up empty dispatcher entries
        if not self._subscriptions[dispatcher]:
            del self._subscriptions[dispatcher]
    
    def unsubscribe_all(self) -> None:
        """
        Unsubscribe this logger from all event types on all dispatchers.
        
        This method provides a convenient way to clean up all subscriptions,
        useful for shutdown procedures or when the logger is no longer needed.
        
        Returns:
            None
        """
        # Create a copy of the subscriptions to avoid modification during iteration
        subscriptions_copy = dict(self._subscriptions)
        
        for dispatcher, event_types in subscriptions_copy.items():
            # Unsubscribe from all event types for this dispatcher
            event_types_list = list(event_types)
            self.unsubscribe_from(dispatcher, *event_types_list)
    
    def get_active_subscriptions(self) -> Dict[Any, List[str]]:
        """
        Get a summary of all active subscriptions.
        
        Returns a dictionary showing which dispatchers this logger is
        subscribed to and what event types it's listening for.
        
        Returns:
            Dict[Any, List[str]]: Dictionary mapping dispatchers to lists of
                                 subscribed event types.
        """
        return {dispatcher: list(event_types) for dispatcher, event_types in self._subscriptions.items()}
    
    def is_subscribed_to(self, dispatcher, event_type: str) -> bool:
        """
        Check if this logger is subscribed to a specific event type on a dispatcher.
        
        Args:
            dispatcher: EventDispatcher to check
            event_type (str): Event type to check for subscription
            
        Returns:
            bool: True if subscribed to the event type on the dispatcher, False otherwise.
            
        Examples:
            >>> if logger.is_subscribed_to(dispatcher, 'error'):
            ...     print("Logger will handle error events")
        """
        return (dispatcher in self._subscriptions and 
                event_type in self._subscriptions[dispatcher])
    
    def on_event(self, data: Dict[str, Any]) -> None:
        """
        Process and display operation events based on their type.
        
        This method serves as the main entry point for event processing,
        routing events to appropriate handlers based on the event type.
        This method is called automatically by dispatchers when subscribed
        events are dispatched.
        
        Args:
            data (Dict[str, Any]): Event data dictionary containing:
                - event_type (str): Type of event (e.g., 'start', 'end', 'error')
                - event_message (str | List[Dict]): Event message or traceback data
                - Additional fields depending on event type
                
        Returns:
            None
            
        Note:
            Error events are handled separately with enhanced formatting,
            while regular events receive standard formatting. This method
            should not raise exceptions to avoid disrupting other subscribers.
        """
        try:
            event_type: str = data.get("event_type", "Unknown event type")
            
            if event_type == EVENT_ERROR:
                self._handle_error_event(data)
            else:
                # Handle regular (non-error) events
                self._handle_regular_event(data)
                
        except Exception as e:
            # Catch any exceptions to prevent disrupting other subscribers
            self._pretty_print(str(e), "PrintLogger internal error: ")

    def _handle_regular_event(self, data: Dict[str, Any]) -> None:
        """
        Handle regular (non-error) operation events.
        
        Formats and displays standard operation events with consistent styling
        and proper text wrapping.
        
        Args:
            data (Dict[str, Any]): Event data containing event_type and event_message
            
        Returns:
            None
        """
        event_type: str = data.get("event_type", "Unknown event type")
        event_message: str = data.get("event_message", "Unknown event message")
        
        # Format based on event type for better readability
        if event_type.endswith('_start') or event_type == 'start':
            self._pretty_print(event_message, "▶ START: ")
        elif event_type.endswith('_end') or event_type == 'end':
            self._pretty_print(event_message, "✓ END: ")
        else:
            self._pretty_print(event_message, f"● {event_type.upper()}: ")

    def _handle_error_event(self, data: Dict[str, Any]) -> None:
        """
        Handle error events with detailed traceback information.
        
        This method processes error events by extracting exception details
        and formatting traceback information for clear console output with
        proper text wrapping.
        
        Args:
            data (Dict[str, Any]): Error event data containing:
                - event_message (List[Dict[str, Any]]): List of traceback frame dictionaries
                - exception_type (str): Name of the exception class
                - exception_str (str): String representation of the exception
                
        Returns:
            None
            
        Note:
            Each traceback frame dictionary should contain:
            - filename (str): Source file path
            - line_number (int): Line number where error occurred
            - function_name (str): Name of the function containing the error
        """
        # Extract exception details with type-safe defaults
        exception_type: str = data.get('exception_type', 'Unknown Exception')
        exception_str: str = data.get('exception_str', 'Unknown error')
        traceback_info: Union[List[Dict[str, Any]], Any] = data.get('event_message', [])
        
        # Display the primary error message with prominent styling and text wrapping
        self._pretty_print(f"\n{'='*self._max_width}")
        self._pretty_print(exception_type, "✗ ERROR: ")
        self._pretty_print(exception_str, "Message: ")
        self._pretty_print(f"{'='*self._max_width}")
        
        # Process and display traceback information if available
        self._print_traceback(traceback_info)
        self._pretty_print(f"{'='*self._max_width}\n")

    def _print_traceback(self, traceback_info: Union[List[Dict[str, Any]], Any]) -> None:
        """
        Format and print traceback information to the console with proper wrapping.
        
        Args:
            traceback_info (Union[List[Dict[str, Any]], Any]): Traceback data,
                expected to be a list of dictionaries containing frame information
                
        Returns:
            None
        """
        if isinstance(traceback_info, list) and traceback_info:
            self._pretty_print("Traceback (most recent call last):")
            
            for trace_item in traceback_info:
                if isinstance(trace_item, dict):
                    # Extract frame information with safe defaults
                    filename: str = trace_item.get('filename', 'unknown')
                    line_number: Union[int, str] = trace_item.get('line_number', '?')
                    function_name: str = trace_item.get('function_name', 'unknown')
                    
                    # Format filename for better readability (show only filename, not full path)
                    display_filename = filename.split('/')[-1] if '/' in filename else filename
                    
                    # Create the traceback line
                    trace_line = f"{display_filename}:{line_number} in {function_name}()"
                    
                    # Pretty print
                    self._pretty_print(trace_line, "→ ")
        else:
            self._pretty_print(traceback_info)