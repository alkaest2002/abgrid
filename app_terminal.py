"""
Terminal application for ABGrid project management.

Author: Pierpaolo Calanna
Date Created: Wed Jun 25 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import re
import argparse
from pathlib import Path
from typing import List, Iterator
from lib.interfaces.terminal.terminal_main import TerminalMain
from lib.utils import check_python_version

# Available languages
LANGUAGES = ["en", "it"]

def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(prog="ABGrid")
    
    parser.add_argument("-a", "--action", required=True, 
                        choices=["init", "groups", "sheets", "reports", "batch"], 
                        help="Action to perform: 'init', 'groups', 'sheets', 'reports', or 'batch'.")
    parser.add_argument("-p", "--project", required=True, 
                        help="Name of the project.")
    parser.add_argument("-g", "--groups", type=int, choices=range(1, 51), default=1,
                        help="Number of groups (1 to 50).")
    parser.add_argument("-m", "--members_per_group", type=int, choices=range(6, 51), default=8,
                        help="Number of members per group (6 to 50).")
    parser.add_argument("-u", "--user", type=str, required=True, 
                        help="Root folder where data is stored.")
    parser.add_argument("-l", "--language", choices=LANGUAGES, default="en", 
                        help="Language used for generating documents.")
    parser.add_argument("-s", "--with-sociogram", action='store_true',
                        help="Output sociogram")
    
    return parser

def get_group_filepaths(project_folderpath: Path) -> List[Path]:
    """Get list of group file paths matching the pattern.
    
    Args:
        project_folderpath: Path to the project folder
        
    Returns:
        List of group file paths
    """
    return [path for path in project_folderpath.glob("*_g*.*") 
            if re.search(r"_g\d+\.\w+$", path.name)]

def get_folders_to_process(data_folder: Path) -> Iterator[Path]:
    """Get folders to process in batch mode.
    
    Args:
        data_folder: Path to the user data folder
        
    Yields:
        Directory paths to process
    """
    return (path for path in data_folder.glob("*") if path.is_dir())

def handle_init_action(project: str, project_folderpath: Path, language: str) -> None:
    """Handle project initialization.
    
    Args:
        project: Project name
        project_folderpath: Path to the project folder
        language: Language for document generation
        
    Raises:
        FileExistsError: If project already exists
    """
    if project_folderpath.exists():
        raise FileExistsError(f"{project} already exists.")
    
    TerminalMain.init_project(project, project_folderpath, language)

def handle_batch_processing(data_folder: Path, with_sociogram: bool, language: str) -> None:
    """Handle batch processing of projects.
    
    Args:
        data_folder: Path to the user data folder
        with_sociogram: Whether to include sociogram in reports
        language: Language for document generation
    """
    for project_folder_path in get_folders_to_process(data_folder):
        project = project_folder_path.name
        project_filepath = next(project_folder_path.glob(f"{project}.*"))
        groups_filepaths = get_group_filepaths(project_folder_path)
        
        terminal_main = TerminalMain(project, project_folder_path, 
                                   project_filepath, groups_filepaths, language)
        terminal_main.generate_reports(with_sociogram)

def handle_project_actions(args: argparse.Namespace, project_folderpath: Path) -> None:
    """Handle individual project actions.
    
    Args:
        args: Parsed command line arguments
        project_folderpath: Path to the project folder
    """
    project_filepath = next(project_folderpath.glob(f"{args.project}.*"))
    groups_filepaths = get_group_filepaths(project_folderpath)
    groups_already_created = len(groups_filepaths)
    groups_to_create = range(groups_already_created + 1, 
                           groups_already_created + args.groups + 1)
    
    terminal_main = TerminalMain(args.project, project_folderpath, 
                               project_filepath, groups_filepaths, args.language)
    
    match args.action:
        case "groups":
            terminal_main.generate_group_inputs(groups_to_create, args.members_per_group, args.language)
        case "sheets":
            terminal_main.generate_answersheets()
        case "reports":
            terminal_main.generate_reports(args.with_sociogram)

def main() -> None:
    """Main application entry point."""
    
    # Check python version (3.10 or higher is needed)
    check_python_version()
    
    # Parse arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    try:
        # Setup the path to the project folder
        project_folderpath = Path("./data") / args.user / args.project
        
        if args.action == "init":
            handle_init_action(args.project, project_folderpath, args.language)
        elif args.action == "batch":
            data_folder = Path("./data") / args.user
            handle_batch_processing(data_folder, args.with_sociogram, args.language)
        else:
            handle_project_actions(args, project_folderpath)
            
    except Exception as error:
        pass

if __name__ == "__main__":
    main()
