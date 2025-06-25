"""
Event-driven logging system for AB-Grid project operations.

This module provides a decorator-based notification system using event emitters
and listeners to track function execution with structured logging capabilities.

Author: Pierpaolo Calanna
Date Created: May 3, 2025
License: MIT License
"""

from typing import Any, Dict, List, Union
from lib import EVENT_ERROR


class PrintLogger:
    """
    Console logger implementing EventListener protocol.
    
    This class handles operation lifecycle events by printing formatted messages
    to the console, including detailed error information with traceback data
    when errors occur.
    
    The logger distinguishes between regular operation events and error events,
    providing appropriate formatting for each type.
    """
    
    def handle_event(self, data: Dict[str, Any]) -> None:
        """
        Process and display operation events based on their type.
        
        This method serves as the main entry point for event processing,
        routing events to appropriate handlers based on the event type.
        
        Args:
            data (Dict[str, Any]): Event data dictionary containing:
                - event_type (str): Type of event (e.g., 'start', 'end', 'error')
                - event_message (str | List[Dict]): Event message or traceback data
                - Additional fields depending on event type
                
        Returns:
            None
            
        Note:
            Error events are handled separately with enhanced formatting,
            while regular events receive standard formatting.
        """
        event_type: str = data.get("event_type", "Unknown event type")
        
        if event_type == EVENT_ERROR:
            self._handle_error_event(data)
        else:
            # Handle regular (non-error) events
            event_message: str = data.get("event_message", "Unknown event message")
            print(f"▶ '{event_type}' - {event_message}")

    def _handle_error_event(self, data: Dict[str, Any]) -> None:
        """
        Handle error events with detailed traceback information.
        
        This method processes error events by extracting exception details
        and formatting traceback information for clear console output.
        
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
        
        # Display the primary error message
        print(f"✗ Error: {exception_type} - {exception_str}")
        
        # Process and display traceback information if available
        self._print_traceback(traceback_info)

    def _print_traceback(self, traceback_info: Union[List[Dict[str, Any]], Any]) -> None:
        """
        Format and print traceback information to the console.
        
        Args:
            traceback_info (Union[List[Dict[str, Any]], Any]): Traceback data,
                expected to be a list of dictionaries containing frame information
                
        Returns:
            None
        """
        if isinstance(traceback_info, list) and traceback_info:
            print("Traceback (most recent call last):")
            
            for trace_item in traceback_info:
                if isinstance(trace_item, dict):
                    # Extract frame information with safe defaults
                    filename: str = trace_item.get('filename', 'unknown')
                    line_number: Union[int, str] = trace_item.get('line_number', '?')
                    function_name: str = trace_item.get('function_name', 'unknown')
                    
                    # Format and display the traceback frame
                    print(f"    → {filename}:{line_number} in {function_name}")
        else:
            print("  (No traceback information available)")
