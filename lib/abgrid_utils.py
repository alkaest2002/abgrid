from typing import Callable, Any
import traceback

def notify_decorator(argument: str) -> Callable:
    def decorator(function: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function executed in place of the original function.

            It adds print notifications before and after function execution.

            Args:
                *args (Any): Positional arguments to pass to the original function.
                **kwargs (Any): Keyword arguments to pass to the original function.

            Returns:
                Any: The result of the original function execution.

            Exceptions:
                Prints an error message if the original function raises an exception,
                along with the traceback details.
            """
            print(f"Operation '{argument}' is being currently executed.")
            try:
                result = function(*args, **kwargs)  # Call the original function
                print(f"Operation '{argument}' was successfully executed.")
                return result
            except Exception as error:
                print(f"Error while executing operation '{argument}'. Error details: {error}")
                print("Traceback details:")
                traceback.print_exc()
        
        return wrapper
    
    return decorator
