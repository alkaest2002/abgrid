"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: T201
import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from lib.interfaces.terminal.terminal_commands import (
    BatchCommand,
    Command,
    GroupCommand,
    InitCommand,
    ReportCommand,
)
from lib.interfaces.terminal.terminal_errors import (
    ABGridError,
    InvalidArgumentError,
)
from lib.utils import check_python_version


# Exit codes
EXIT_SUCCESS: int = 0
EXIT_APP_ERROR: int = 1
EXIT_SYSTEM_ERROR: int = 2
EXIT_USER_INTERRUPT: int = 130


@dataclass
class Config:
    """Application configuration settings container.

    Defines default values and constraints for AB-Grid application settings
    including supported languages, group size limits, and file system paths.
    """
    data_path: Path = Path("./data")
    languages: list[str] = field(default_factory=lambda: ["en", "it"])
    min_members: int = 8
    max_members: int = 50


class TerminalApp:
    """Main application class for AB-Grid terminal interface.

    Orchestrates the entire command-line application workflow including
    argument parsing, validation, command dispatch, and comprehensive
    error handling with appropriate exit codes.
    """

    def __init__(self, config: Config) -> None:
        """Initialize the AB-Grid terminal application.

        Sets up the application configuration and command registry,
        mapping action names to their corresponding command classes.

        Args:
            config: Custom configuration for the application.

        Returns:
            None.
        """
        self.config = config
        self.commands: dict[str, type[Command]] = {
            "init": InitCommand,
            "group": GroupCommand,
            "report": ReportCommand,
            "batch": BatchCommand
        }

    def run(self) -> int:
        """Main application entry point with comprehensive error handling.

        Executes the complete application workflow including Python version
        checking, argument parsing and validation, command execution, and
        error handling with appropriate exit codes.

        Returns:
            Integer exit code:
            - EXIT_SUCCESS (0): Successful execution.
            - EXIT_APP_ERROR (1): Application-specific error.
            - EXIT_SYSTEM_ERROR (2): Unexpected system error.
            - EXIT_USER_INTERRUPT (130): User cancelled operation.

        Notes:
            - Handles all exception types with appropriate user feedback.
            - Provides clean exit codes for shell script integration.
            - Supports keyboard interrupt (Ctrl+C) handling.
        """
        try:
            check_python_version()
            args = self._parse_args()
            self._validate_args(args)

            command = self.commands[args.action](args, self.config)
            command.execute()

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return EXIT_USER_INTERRUPT
        except ABGridError as error:
            print(f"Error: {error}")
            return EXIT_APP_ERROR
        except Exception as error:
            print(f"Unexpected error: {error}")
            return EXIT_SYSTEM_ERROR
        else:
            return EXIT_SUCCESS

    ##################################################################################################################
    #   PRIVATE METHODS
    ##################################################################################################################

    def _parse_args(self) -> argparse.Namespace:
        """Parse and structure command line arguments.

        Defines the complete command-line interface including all arguments,
        their types, constraints, and help documentation. Handles argument
        parsing with built-in validation and help generation.

        Returns:
            Namespace object containing parsed command line arguments

        Notes:
            - Includes comprehensive help text for each argument.
            - Enforces type checking and value constraints.
            - Supports both short and long argument forms where appropriate.
        """
        parser = argparse.ArgumentParser(
            prog="ABGrid",
            description="ABGrid terminal app command line interface",
            epilog="Examples:\n"
                "  abgrid -u user1 -p project1 -a init\n"
                "  abgrid -u user1 -p project1 -m 5 -a group\n"
                "  abgrid -u user1 -p project1 -a report -l en -s\n"
                "  abgrid -u user1 -a batch -l en -s\n",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument("-u", "--user", type=str, required=True,
                          help="Base folder where data is stored.")
        parser.add_argument("-p", "--project", type=str,
                          help="Name of the project.")
        parser.add_argument("-a", "--action", required=True,
                          choices=["init", "group", "report", "batch"],
                          help="Action to perform.")
        parser.add_argument("-m", "--members_per_group", type=int,
                          choices=range(self.config.min_members, self.config.max_members + 1),
                          default=8,
                          help=f"Number of members per group ({self.config.min_members}-{self.config.max_members}).")
        parser.add_argument("-l", "--language", choices=self.config.languages, default="it",
                          help="Language for documents.")
        parser.add_argument("-s", "--with-sociogram", action="store_true",
                          help="Include sociogram in output.")

        return parser.parse_args()

    def _validate_args(self, args: argparse.Namespace) -> None:
        """Validate parsed command line arguments for consistency and requirements.

        Performs additional validation beyond basic argument parsing,
        checking for required argument combinations, character constraints,
        and logical consistency between different arguments.

        Args:
            args: Parsed command line arguments to validate.

        Returns:
            None.

        Raises:
            InvalidArgumentError: If arguments fail validation checks.

        Notes:
            - Ensures project name is provided for actions that require it.
            - Validates user name character constraints for file system safety.
            - Can be extended for additional business logic validation.
        """
        if args.action in ["init", "group", "report"] and not args.project:
            error_message = f"Project name required for {args.action} action"
            raise InvalidArgumentError(error_message)

        if not args.user.replace("_", "").replace("-", "").isalnum():
            error_message = "User name must be alphanumeric with hyphens/underscores only"
            raise InvalidArgumentError(error_message)


def main() -> int:
    """Entry point for the AB-Grid terminal application.

    Creates and runs the main application instance, providing the
    standard entry point for command-line execution with proper
    exit code handling.

    Returns:
        Integer exit code from application execution

    Notes:
        - Designed to be called from command line or shell scripts.
        - Exit codes follow standard Unix conventions.
        - Can be imported and called programmatically if needed.
    """
    app = TerminalApp(Config())
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
