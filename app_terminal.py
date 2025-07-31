"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Type, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from lib.interfaces.terminal.terminal_main import TerminalMain
from lib.utils import check_python_version

# Exit codes
EXIT_SUCCESS: int = 0
EXIT_APP_ERROR: int = 1
EXIT_SYSTEM_ERROR: int = 2
EXIT_USER_INTERRUPT: int = 130


@dataclass
class Config:
    """
    Application configuration settings container.
    
    Defines default values and constraints for AB-Grid application settings
    including supported languages, group size limits, and file system paths.
    """
    data_path: Path = Path("./data")
    languages: List[str] = field(default_factory=lambda: ["en", "it"])
    min_members: int = 8
    max_members: int = 50


class ABGridError(Exception):
    """
    Base exception class for AB-Grid application errors.
    
    Serves as the parent class for all application-specific exceptions,
    providing a common interface for error handling throughout the application.
    """
    pass


class FolderNotFoundError(ABGridError):
    """
    Exception raised when a required directory doesn't exist.
    
    Used specifically for cases where the application expects to find
    an existing folder but it's missing from the file system.
    """
    pass


class FolderAlreadyExistsError(ABGridError):
    """
    Exception raised when attempting to create a project that already exists.
    
    Prevents accidental overwriting of existing project data by failing
    early when duplicate project names are detected.
    """
    pass


class InvalidArgumentError(ABGridError):
    """
    Exception raised when command-line arguments are invalid or malformed.
    
    Handles validation errors for user input including missing required
    arguments, invalid character sets, and constraint violations.
    """
    pass


class Command(ABC):
    """
    Abstract base class for all AB-Grid commands with shared functionality.
    
    Provides common utilities for path management, folder validation,
    and configuration access. All concrete command classes must inherit
    from this base class and implement the execute method.
    """
    
    def __init__(self, args: argparse.Namespace, config: Config) -> None:
        """
        Initialize command with parsed arguments and configuration.
        
        Args:
            args: Parsed command line arguments containing user input
            config: Application configuration with settings and constraints
            
        Returns:
            None
        """
        self.args = args
        self.config = config
    
    @abstractmethod
    def execute(self) -> None:
        """
        Execute the command with specific implementation logic.
        
        Abstract method that must be implemented by all concrete command
        classes to define their specific behavior and operations.
        
        Returns:
            None
            
        Raises:
            NotImplementedError: If called on abstract base class
        """
        pass
    
    def get_user_path(self) -> Path:
        """
        Get the file system path for the current user's data folder.
        
        Constructs the path by combining the configured data directory
        with the user name from command line arguments.
        
        Returns:
            Path object pointing to the user's data directory
        """
        return self.config.data_path / self.args.user
    
    def get_project_path(self) -> Path:
        """
        Get the file system path for the current project folder.
        
        Constructs the full project path by combining user path
        with the project name from command line arguments.
        
        Returns:
            Path object pointing to the specific project directory
        """
        return self.get_user_path() / self.args.project
    
    def ensure_folder_exists(self, path: Path) -> None:
        """
        Validate that the specified folder exists on the file system.
        
        Performs existence check and raises appropriate exception if
        the folder is not found, providing clear error messaging.
        
        Args:
            path: Path object to validate for existence
            
        Returns:
            None
            
        Raises:
            FolderNotFoundError: If the specified folder doesn't exist
        """
        if not path.exists():
            raise FolderNotFoundError(f"Folder '{path.name}' not found at {path}")
    
    def ensure_folder_not_exists(self, path: Path) -> None:
        """
        Validate that the specified folder doesn't exist on the file system.
        
        Prevents accidental overwriting by checking for existing folders
        and raising an exception if a conflict is detected.
        
        Args:
            path: Path object to validate for non-existence
            
        Returns:
            None
            
        Raises:
            FolderAlreadyExistsError: If the specified folder already exists
        """
        if path.exists():
            raise FolderAlreadyExistsError(f"Project '{path.name}' already exists at {path}")


class InitCommand(Command):
    """
    Command for initializing new AB-Grid projects.
    
    Creates the directory structure and initial configuration files
    required for a new AB-Grid project, ensuring no conflicts with
    existing projects.
    """
    
    def execute(self) -> None:
        """
        Execute project initialization with directory structure creation.
        
        Validates that the project doesn't already exist, then creates
        the necessary folder structure and configuration files for a
        new AB-Grid project.
        
        Returns:
            None
            
        Raises:
            FolderAlreadyExistsError: If project already exists
        """
        project_path = self.get_project_path()
        self.ensure_folder_not_exists(project_path)
        
        terminal_main = TerminalMain(self.args)
        terminal_main.init_project()
        print(f"Project '{self.args.project}' initialized successfully")


class GroupCommand(Command):
    """
    Command for generating group configuration files.
    
    Creates YAML configuration files for new groups within an existing
    AB-Grid project, using language-specific templates and ensuring
    proper group numbering.
    """
    
    def execute(self) -> None:
        """
        Execute group generation for the specified project.
        
        Validates that the target project exists, then generates
        a new group configuration file with appropriate numbering
        and template data.
        
        Returns:
            None
            
        Raises:
            FolderNotFoundError: If the target project doesn't exist
        """
        project_path = self.get_project_path()
        self.ensure_folder_exists(project_path)
        
        terminal_main = TerminalMain(self.args)
        terminal_main.generate_group()
        print(f"Generated group for project '{self.args.project}'")


class ReportCommand(Command):
    """
    Command for generating comprehensive project reports.
    
    Processes group data files to create detailed PDF reports with
    statistical analysis, social network metrics, and optional
    sociogram visualizations.
    """
    
    def execute(self) -> None:
        """
        Execute report generation for the specified project.
        
        Validates project existence, processes all group files,
        and generates comprehensive reports with optional sociograms
        and JSON data exports.
        
        Returns:
            None
            
        Raises:
            FolderNotFoundError: If the target project doesn't exist
            ABGridError: If no group files are found in the project
        """
        project_path = self.get_project_path()
        self.ensure_folder_exists(project_path)
        
        terminal_main = TerminalMain(self.args)
        terminal_main.generate_report()
        
        sociogram_text = " with sociogram" if self.args.with_sociogram else ""
        print(f"Generated report{sociogram_text} for project '{self.args.project}'")


class BatchCommand(Command):
    """
    Command for processing multiple projects in batch mode.
    
    Automatically discovers and processes all projects within a user's
    directory, generating reports for each project with error handling
    and progress reporting.
    """
    
    def execute(self) -> None:
        """
        Execute batch processing for all projects in the user directory.
        
        Discovers all project folders, processes each one individually
        with error handling, and provides summary statistics of the
        batch operation results.
        
        Returns:
            None
            
        Notes:
            - Continues processing remaining projects if individual failures occur
            - Provides detailed progress feedback and error reporting
            - Summarizes total processed and failed project counts
            
        Raises:
            FolderNotFoundError: If the user directory doesn't exist
        """
        user_path = self.get_user_path()
        self.ensure_folder_exists(user_path)
        
        project_folders = [path for path in user_path.glob("*") if path.is_dir()]
        if not project_folders:
            print(f"No projects found in {user_path}")
            return
        
        processed_count = 0
        failed_count = 0
        
        for project_folder in project_folders:
            try:
                # Create args for this project
                project_args = argparse.Namespace(**vars(self.args))
                project_args.project = project_folder.name
                project_args.action = "report"
                
                terminal_main = TerminalMain(project_args)
                terminal_main.generate_report()
                processed_count += 1
                print(f"Processed project '{project_folder.name}'")
                
            except Exception as e:
                failed_count += 1
                print(f"Error processing project '{project_folder.name}': {e}")
        
        # Print summary
        sociogram_text = " with sociograms" if self.args.with_sociogram else ""
        print(f"Batch processing complete. Processed {processed_count} project(s){sociogram_text}")
        if failed_count > 0:
            print(f"Failed to process {failed_count} project(s)")


class ABGridTerminalApp:
    """
    Main application class for AB-Grid terminal interface.
    
    Orchestrates the entire command-line application workflow including
    argument parsing, validation, command dispatch, and comprehensive
    error handling with appropriate exit codes.
    """
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize the AB-Grid terminal application.
        
        Sets up the application configuration and command registry,
        mapping action names to their corresponding command classes.
        
        Args:
            config: Optional custom configuration. If None, uses default Config()
            
        Returns:
            None
        """
        self.config = config or Config()
        self.commands: Dict[str, Type[Command]] = {
            "init": InitCommand,
            "group": GroupCommand,
            "report": ReportCommand,
            "batch": BatchCommand
        }
    
    def run(self) -> int:
        """
        Main application entry point with comprehensive error handling.
        
        Executes the complete application workflow including Python version
        checking, argument parsing and validation, command execution, and
        error handling with appropriate exit codes.
        
        Returns:
            Integer exit code:
            - EXIT_SUCCESS (0): Successful execution
            - EXIT_APP_ERROR (1): Application-specific error
            - EXIT_SYSTEM_ERROR (2): Unexpected system error
            - EXIT_USER_INTERRUPT (130): User cancelled operation
            
        Notes:
            - Handles all exception types with appropriate user feedback
            - Provides clean exit codes for shell script integration
            - Supports keyboard interrupt (Ctrl+C) handling
        """
        try:
            check_python_version()
            args = self.parse_args()
            self.validate_args(args)
            
            command = self.commands[args.action](args, self.config)
            command.execute()
            return EXIT_SUCCESS
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return EXIT_USER_INTERRUPT
        except ABGridError as error:
            print(f"Error: {error}")
            return EXIT_APP_ERROR
        except Exception as error:
            print(f"Unexpected error: {error}")
            return EXIT_SYSTEM_ERROR
    
    def parse_args(self) -> argparse.Namespace:
        """
        Parse and structure command line arguments.
        
        Defines the complete command-line interface including all arguments,
        their types, constraints, and help documentation. Handles argument
        parsing with built-in validation and help generation.
        
        Returns:
            Namespace object containing parsed command line arguments
            
        Notes:
            - Includes comprehensive help text for each argument
            - Enforces type checking and value constraints
            - Supports both short and long argument forms where appropriate
        """
        parser = argparse.ArgumentParser(prog="ABGrid")
        
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
        parser.add_argument("-s", "--with-sociogram", action='store_true',
                          help="Include sociogram in output.")
        
        return parser.parse_args()
    
    def validate_args(self, args: argparse.Namespace) -> None:
        """
        Validate parsed command line arguments for consistency and requirements.
        
        Performs additional validation beyond basic argument parsing,
        checking for required argument combinations, character constraints,
        and logical consistency between different arguments.
        
        Args:
            args: Parsed command line arguments to validate
            
        Returns:
            None
            
        Raises:
            InvalidArgumentError: If arguments fail validation checks
            
        Notes:
            - Ensures project name is provided for actions that require it
            - Validates user name character constraints for file system safety
            - Can be extended for additional business logic validation
        """
        if args.action in ["init", "group", "report"] and not args.project:
            raise InvalidArgumentError(f"Project name required for {args.action} action")
        
        if not args.user.replace('_', '').replace('-', '').isalnum():
            raise InvalidArgumentError("User name must be alphanumeric with hyphens/underscores only")


def main() -> int:
    """
    Entry point for the AB-Grid terminal application.
    
    Creates and runs the main application instance, providing the
    standard entry point for command-line execution with proper
    exit code handling.
    
    Returns:
        Integer exit code from application execution
        
    Notes:
        - Designed to be called from command line or shell scripts
        - Exit codes follow standard Unix conventions
        - Can be imported and called programmatically if needed
    """
    app = ABGridTerminalApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
