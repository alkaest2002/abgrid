"""
Event-driven logging system for AB-Grid project operations.

This module provides a decorator-based notification system using event emitters
and listeners to track function execution with structured logging capabilities.

Author: Pierpaolo Calanna
Date Created: May 3, 2025
License: MIT License
"""

from typing import Any, Dict
from lib import EVENT_ERROR

class PrintLogger:
    """
    Console logger implementing EventListener protocol.
    
    Handles operation lifecycle events by printing formatted messages
    including error details and traceback information when applicable.
    """
    
    def handle_event(self, data: Dict[str, Any]) -> None:
        """
        Process operation events and print appropriate messages.
        
        Args:
            data: Event data containing 'event_type', 'event_message' and other details
        """
        event_type = data.get("event_type", "Unknown event type")
        event_message = data.get("event_message", "Unknown event message")

        # Handle different event types
        if event_type == EVENT_ERROR:
            self._handle_error_event(data)
        else:
            # Handle regular events
            event_message = data.get("event_message", "Unknown event message")
            print(f"▶ '{event_type}' - {event_message}")

    def _handle_error_event(self, data: Dict[str, Any]) -> None:
        """
        Handle error events with detailed traceback information.
        
        Args:
            data: Error event data from the decorator containing:
                  - event_message: List of traceback dictionaries
                  - exception_type: Type of exception
                  - exception_str: String representation of exception
        """
        exception_type = data.get('exception_type', 'Unknown Exception')
        exception_str = data.get('exception_str', 'Unknown error')
        traceback_info = data.get('event_message', [])  # The traceback list
        
        # Print main error message
        print(f"✗ Error: {exception_type} - {exception_str}")
        
        # Print simplified traceback if available
        if isinstance(traceback_info, list) and traceback_info:
            print("  Traceback (most recent call last):")
            for trace_item in traceback_info:
                if isinstance(trace_item, dict):
                    filename = trace_item.get('filename', 'unknown')
                    line_number = trace_item.get('line_number', '?')
                    function_name = trace_item.get('function_name', 'unknown')
                    print(f"    → {filename}:{line_number} in {function_name}")
        else:
            print("(No traceback information available)")
