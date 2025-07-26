"""
Filename: app_terminal.py

Description: Command-line interface for AB-Grid project management, providing initialization, data processing, and batch report generation capabilities.

Author: Pierpaolo Calanna

Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Iterator
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from lib.interfaces.terminal.terminal_main import TerminalMain
from lib.utils import check_python_version

EXIT_SUCCESS = 0
EXIT_APP_ERROR = 1
EXIT_SYSTEM_ERROR = 2
EXIT_USER_INTERRUPT = 130

@dataclass
class Config:
    """
    Application configuration settings.
    
    Contains default paths, supported languages, and validation ranges
    for command-line arguments.
    """
    data_path: Path = Path("./data")
    languages: List[str] = field(default_factory=lambda: ["en", "it"])
    min_members: int = 8
    max_members: int = 50


class ABGridError(Exception):
    """
    Base exception for AB-Grid application.
    
    All custom exceptions in the application inherit from this base class
    to provide consistent error handling and categorization.
    """
    pass


class FolderNotFoundError(ABGridError):
    """
    Raised when folder doesn't exist.
    
    Thrown when attempting to perform operations on non-existent projects,
    typically during group, report, or batch operations.
    """
    pass


class FolderAlreadyExistsError(ABGridError):
    """
    Raised when trying to create existing project.
    
    Thrown during project initialization when a project with the same
    name already exists in the specified location.
    """
    pass


class InvalidArgumentError(ABGridError):
    """
    Raised when arguments are invalid.
    
    Thrown when command-line arguments fail validation rules,
    such as missing required parameters or conflicting options.
    """
    pass


class Command(ABC):
    """
    Abstract base class for commands.
    
    Implements the Command pattern to encapsulate different actions
    (init, group, report, batch) as discrete command objects with
    consistent execution interface.
    """
    
    def __init__(self, args: argparse.Namespace) -> None:
        """
        Initialize command with parsed arguments.
        
        Args:
            args: Parsed command-line arguments containing all configuration
        
        Returns:
            None
        """
        self.args = args
    
    @abstractmethod
    def execute(self) -> None:
        """
        Execute the command.
        
        Abstract method that must be implemented by concrete command classes
        to perform their specific operations.
        
        Returns:
            None
            
        Raises:
            ABGridError: For application-specific errors
            Exception: For unexpected system errors
        """
        pass


class InitCommand(Command):
    """
    Command to initialize a new project.
    
    Creates a new AB-Grid project with the required directory structure
    and initializes it for group creation and report generation.
    """
    
    def execute(self) -> None:
        """
        Execute project initialization.
        
        Creates project directory structure and validates that the project
        doesn't already exist.
        
        Returns:
            None
            
        Raises:
            FolderAlreadyExistsError: If project already exists
        """
        project_folderpath = _get_project_folderpath(self.args)
        _ensure_folder_not_exists(project_folderpath)
        TerminalMain.init_project(project_folderpath)
        print(f"Project '{self.args.project}' initialized successfully")


class GroupCommand(Command):
    """
    Command to generate groups for a project.
    
    Creates new group configuration files for an existing project,
    allowing users to define group members and settings.
    """
    
    def execute(self) -> None:
        """
        Execute group generation.
        
        Validates project exists and creates a new group configuration
        file with the specified number of members.
        
        Returns:
            None
            
        Raises:
            FolderNotFoundError: If project doesn't exist
        """
        project_folderpath = _get_project_folderpath(self.args)
        _ensure_folder_exists(project_folderpath)
        terminal_main = TerminalMain(self.args)
        terminal_main.generate_group()
        print(f"Generated group for project '{self.args.project}'")


class ReportCommand(Command):
    """
    Command to generate reports for a project.
    
    Processes all group files in a project and generates comprehensive
    PDF reports with optional sociogram visualizations.
    """
    
    def execute(self) -> None:
        """
        Execute report generation.
        
        Validates project exists and generates reports for all groups
        within the project, with optional sociogram inclusion.
        
        Returns:
            None
            
        Raises:
            FolderNotFoundError: If project doesn't exist
            ABGridError: If no group files found
        """
        project_folderpath = _get_project_folderpath(self.args)
        _ensure_folder_exists(project_folderpath)
        terminal_main = TerminalMain(self.args)
        terminal_main.generate_report()
        sociogram_text = " with sociogram" if self.args.with_sociogram else ""
        print(f"Generated report{sociogram_text} for project '{self.args.project}'")


class BatchCommand(Command):
    """
    Command to process multiple projects in batch.
    
    Iterates through all projects in the user's data folder and generates
    reports for each project that contains group files.
    """
    
    def execute(self) -> None:
        """
        Execute batch processing.
        
        Processes all projects in the user's data folder, generating reports
        for each project. Continues processing even if individual projects fail.
        
        Returns:
            None
            
        Raises:
            ABGridError: If user data folder doesn't exist
            
        Notes:
            - Individual project failures don't stop batch processing
            - Provides summary of successful and failed processing
        """
        data_folderpath = _get_user_folderpath(self.args)
        _ensure_folder_exists(data_folderpath)
        
        project_folders = [path for path in data_folderpath.glob("*") if path.is_dir()]
        if not project_folders:
            print(f"No projects found in {data_folderpath}")
            return
        
        processed_count = 0
        failed_count = 0
        
        for project_folderpath in project_folders:
            try:
                # Create a modified args object for each project
                project_args = argparse.Namespace(**vars(self.args))
                project_args.project = project_folderpath.name
                # Treat each batch item as a report action
                project_args.action = "report"  
                
                # Create TerminalMain instance with project-specific args
                terminal_main = TerminalMain(project_args)
                terminal_main.generate_report()
                
                processed_count += 1
                print(f"Processed project '{project_folderpath.name}'")
                
            except Exception as e:
                failed_count += 1
                print(f"Error processing project '{project_folderpath.name}': {e}")
                # Continue with the next project instead of stopping
                continue
        
        # Summary report
        sociogram_text = " with sociograms" if self.args.with_sociogram else ""
        
        print(f"Batch processing complete. Processed {processed_count} project(s){sociogram_text}")
        
        if failed_count > 0:
            print(f"Failed to process {failed_count} project(s)")

# Init config
config = Config()


def main() -> int:
    """
    Main application entry point.
    
    Orchestrates the complete application flow from argument parsing
    through command execution, with comprehensive error handling.
    
    Returns:
        Exit code: 
            0 for success, 
            1 for application errors, 
            2 for unexpected errors,
            130 for user interruption
                  
    Notes:
        - Handles KeyboardInterrupt gracefully
        - Distinguishes between application and system errors
        - Provides appropriate exit codes for shell integration
    """
    try:
        # Ensure python compatibility
        check_python_version()

        # Parse and validate user argumets
        parser = _setup_argument_parser()
        args = parser.parse_args()
        _validate_args(args)

        # Create and execute command
        command = _create_command(args)
        command.execute()

        return EXIT_SUCCESS

    # Interrupt   
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return EXIT_USER_INTERRUPT
    # App error
    except ABGridError as error:
        print(f"Error: {error}")
        return EXIT_APP_ERROR
    # System error
    except Exception as error:
        print(f"Unexpected error: {error}")
        return EXIT_SYSTEM_ERROR

def _setup_argument_parser() -> argparse.ArgumentParser:
    """
    Set up and configure the argument parser.
    
    Creates and configures an ArgumentParser instance with all required
    and optional command-line arguments for the AB-Grid application.
    
    Returns:
        Configured ArgumentParser instance ready for parsing command-line arguments
        
    Notes:
        - Uses configuration values for validation ranges and choices
        - Arguments are organized by frequency of use and logical grouping
    """
    parser = argparse.ArgumentParser(prog="ABGrid")

    parser.add_argument("-u", "--user", type=str, required=True, 
                        help="Base folder where data is stored.")
    parser.add_argument("-p", "--project", 
                        help="Name of the project.")
    parser.add_argument("-a", "--action", required=True, 
                        choices=["init", "group", "report", "batch"], 
                        help="Action to perform: 'init', 'group', 'report', or 'batch'.")
    parser.add_argument("-m", "--members_per_group", type=int, 
                        choices=range(config.min_members, config.max_members + 1), 
                        default=8, 
                        help=f"Number of members per group ({config.min_members} to {config.max_members}).")
    parser.add_argument("-l", "--language", choices=config.languages, default="it", 
                        help="Language used for generating documents.")
    parser.add_argument("-s", "--with-sociogram", action='store_true', 
                        help="Output sociogram")
    
    return parser


# Private helper functions
def _validate_args(args: argparse.Namespace) -> None:
    """
    Validate command line arguments.
    
    Performs cross-argument validation to ensure argument combinations
    are valid for the specified action.
    
    Args:
        args: Parsed command-line arguments to validate
        
    Returns:
        None
        
    Raises:
        InvalidArgumentError: If argument validation fails
        
    Notes:
        - init, group, report actions require project name
    """
    if args.action in ["init", "group", "report"] and not args.project:
        raise InvalidArgumentError(f"Project name is required for {args.action} action")
    
    if args.user and not args.user.replace('_', '').replace('-', '').isalnum():
        raise InvalidArgumentError("User name should contain only alphanumeric characters, hyphens, and underscores")



def _create_command(args: argparse.Namespace) -> Command:
    """
    Factory function to create commands.
    
    Creates and returns the appropriate command instance based on the
    action specified in the arguments.
    
    Args:
        args: Parsed command-line arguments containing action type
        
    Returns:
        Command instance corresponding to the specified action
        
    Notes:
        - Uses dictionary mapping for efficient command selection
        - All commands follow the same Command interface
    """
    command_map = {
        "init": InitCommand,
        "group": GroupCommand,
        "report": ReportCommand,
        "batch": BatchCommand
    }
    return command_map[args.action](args)


def _get_user_folderpath(args: argparse.Namespace) -> Path:
    """
    Get user data folder path.
    
    Constructs the path to the user's data folder based on the
    configured data path and user argument.
    
    Args:
        args: Parsed command-line arguments containing user identifier
        
    Returns:
        Path to the user's data folder
    """
    return config.data_path / args.user


def _get_project_folderpath(args: argparse.Namespace) -> Path:
    """
    Get project folder path.
    
    Constructs the full path to a specific project folder within
    the user's data directory.
    
    Args:
        args: Parsed command-line arguments containing user and project identifiers
        
    Returns:
        Path to the project folder
    """
    return _get_user_folderpath(args) / args.project


def _ensure_folder_exists(folderpath: Path) -> None:
    """
    Validate that project exists for non-init actions.
    
    Checks if the specified project directory exists and raises an
    appropriate error if not found.
    
    Args:
        folderpath: Path to the directory to validate
        
    Returns:
        None
        
    Raises:
        FolderNotFoundError: If the project directory doesn't exist
    """
    if not folderpath.exists():
        raise FolderNotFoundError(f"Project '{folderpath.name}' not found at {folderpath}")


def _ensure_folder_not_exists(project_folderpath: Path) -> None:
    """
    Validate that project doesn't exist for init action.
    
    Checks if the specified project directory already exists and raises
    an error if found, preventing accidental overwrites.
    
    Args:
        project_folderpath: Path to the project directory to validate
        
    Returns:
        None
        
    Raises:
        FolderAlreadyExistsError: If the project directory already exists
    """
    if project_folderpath.exists():
        raise FolderAlreadyExistsError(f"Project '{project_folderpath.name}' already exists at {project_folderpath}")


if __name__ == "__main__":
    sys.exit(main())
