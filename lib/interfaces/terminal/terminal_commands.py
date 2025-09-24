"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: T201
import argparse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from lib.interfaces.terminal.terminal_errors import (
    FolderAlreadyExistsError,
    FolderNotFoundError,
)
from lib.interfaces.terminal.terminal_main import TerminalMain


# Application configuration protocol
class ConfigLike(Protocol):
    """Protocol defining the expected structure of configuration objects."""
    data_path: Path
    languages: list[str]
    min_members: int
    max_members: int


class Command(ABC):
    """Abstract base class for all AB-Grid commands with shared functionality.

    Provides common utilities for path management, folder validation,
    and configuration access. All concrete command classes must inherit
    from this base class and implement the execute method.
    """

    def __init__(self, args: argparse.Namespace, config: ConfigLike) -> None:
        """Initialize command with parsed arguments and configuration.

        Args:
            args: Parsed command line arguments containing user input.
            config: Command configuration.

        Returns:
            None.
        """
        self.args = args
        self.config = config

    @abstractmethod
    def execute(self) -> None:
        """Execute the command with specific implementation logic.

        Abstract method that must be implemented by all concrete command
        classes to define their specific behavior and operations.

        Returns:
            None.

        Raises:
            NotImplementedError: If called on abstract base class.
        """

    ##################################################################################################################
    #   PRIVATE METHODS
    ##################################################################################################################

    def _get_user_path(self) -> Path:
        """Get the file system path for the current user's data folder.

        Constructs the path by combining the configured data directory
        with the user name from command line arguments.

        Returns:
            Path object pointing to the user's data directory
        """
        return self.config.data_path / Path(str(self.args.user))

    def _get_project_path(self) -> Path:
        """Get the file system path for the current project folder.

        Constructs the full project path by combining user path
        with the project name from command line arguments.

        Returns:
            Path object pointing to the specific project directory
        """
        return self._get_user_path() / Path(str(self.args.project))

    def _ensure_folder_exists(self, path: Path) -> None:
        """Validate that the specified folder exists on the file system.

        Performs existence check and raises appropriate exception if
        the folder is not found, providing clear error messaging.

        Args:
            path: Path object to validate for existence.

        Returns:
            None.

        Raises:
            FolderNotFoundError: If the specified folder doesn't exist.
        """
        if not path.exists():
            error_message = f"Folder '{path.name}' not found at {path}"
            raise FolderNotFoundError(error_message)

    def _ensure_folder_not_exists(self, path: Path) -> None:
        """Validate that the specified folder doesn't exist on the file system.

        Prevents accidental overwriting by checking for existing folders
        and raising an exception if a conflict is detected.

        Args:
            path: Path object to validate for non-existence.

        Returns:
            None.

        Raises:
            FolderAlreadyExistsError: If the specified folder already exists.
        """
        if path.exists():
            error_message = f"Project '{path.name}' already exists at {path}"
            raise FolderAlreadyExistsError(error_message)


class InitCommand(Command):
    """Command for initializing new AB-Grid projects.

    Creates the directory structure and initial configuration files
    required for a new AB-Grid project, ensuring no conflicts with
    existing projects.
    """

    def execute(self) -> None:
        """Execute project initialization with directory structure creation.

        Validates that the project doesn't already exist, then creates
        the necessary folder structure and configuration files for a
        new AB-Grid project.

        Returns:
            None.

        Raises:
            FolderAlreadyExistsError: If project already exists.
        """
        project_path = self._get_project_path()
        self._ensure_folder_not_exists(project_path)

        terminal_main = TerminalMain(self.args)
        terminal_main.init_project()
        print(f"Project '{self.args.project}' initialized successfully")


class GroupCommand(Command):
    """Command for generating group configuration files.

    Creates YAML configuration files for new groups within an existing
    AB-Grid project, using language-specific templates and ensuring
    proper group numbering.
    """

    def execute(self) -> None:
        """Execute group generation for the specified project.

        Validates that the target project exists, then generates
        a new group configuration file with appropriate numbering
        and template data.

        Returns:
            None.

        Raises:
            FolderNotFoundError: If the target project doesn't exist.
        """
        project_path = self._get_project_path()
        self._ensure_folder_exists(project_path)

        terminal_main = TerminalMain(self.args)
        terminal_main.generate_group()
        print(f"Generated group for project '{self.args.project}'")


class ReportCommand(Command):
    """Command for generating comprehensive project reports.

    Processes group data files to create detailed PDF reports with
    statistical analysis, social network metrics, and optional
    sociogram visualizations.
    """

    def execute(self) -> None:
        """Execute report generation for the specified project.

        Validates project existence, processes all group files,
        and generates comprehensive reports with optional sociograms
        and JSON data exports.

        Returns:
            None.

        Raises:
            - FolderNotFoundError: If the target project doesn't exist.
            - ABGridError: If no group files are found in the project.
        """
        project_path = self._get_project_path()
        self._ensure_folder_exists(project_path)

        terminal_main = TerminalMain(self.args)
        terminal_main.generate_report()

        sociogram_text = " with sociogram" if self.args.with_sociogram else ""
        print(f"Generated report{sociogram_text} for project '{self.args.project}'")


class BatchCommand(Command):
    """Command for processing multiple projects in batch mode.

    Automatically discovers and processes all projects within a user's
    directory, generating reports for each project with error handling
    and progress reporting.
    """

    def execute(self) -> None:
        """Execute batch processing for all projects in the user directory.

        Discovers all project folders, processes each one individually
        with error handling, and provides summary statistics of the
        batch operation results.

        Returns:
            None.

        Notes:
            - Continues processing remaining projects if individual failures occur.
            - Provides detailed progress feedback and error reporting.
            - Summarizes total processed and failed project counts.

        Raises:
            FolderNotFoundError: If the user directory doesn't exist.
        """
        user_path = self._get_user_path()
        self._ensure_folder_exists(user_path)

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
