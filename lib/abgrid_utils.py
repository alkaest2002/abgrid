from typing import Callable, Any

def notify_decorator(argument: str) -> Callable:
    """
    Decorator to add print notifications before and after the execution of a function.

    Args:
        argument (str): A descriptive string used in the print messages to specify
                        the type of task being carried out (e.g., "project", "report").

    Returns:
        Callable: A decorator function that wraps the original function.
    """
    def decorator(function: Callable) -> Callable:
        """
        Inner decorator function that wraps the target function.

        Args:
            function (Callable): The function to be wrapped.

        Returns:
            Callable: The wrapped function with added print statements.
        """
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
                Prints an error message if the original function raises an exception.
            """
            print(f"Generating {argument} file(s).")
            try:
                result = function(*args, **kwargs)  # Call the original function
                print(f"{argument} file(s) generated.")
                return result
            except Exception as error:
                print(f"Error while generating {argument} file(s). Error is {error}", "\n", error)
        
        return wrapper
    
    return decorator
