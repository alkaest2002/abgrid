import argparse

from pathlib import Path
from lib.abgrid_main import ABGridMain

# Set up the argument parser
parser = argparse.ArgumentParser(prog="ABGrid")

# Add arguments
parser.add_argument("-u", "--user", type=str, required=True, help="Root folder.")
parser.add_argument("-l", "--language", choices=["it", "en"], default="en", help="Language used for reporting.")
parser.add_argument("-s", "--with-sociogram", action='store_true', help="Render sociogram.")

# Parse arguments
args = parser.parse_args()

# Get user root folder
data_folder = Path("./data") / args.user

# Glob folders in user root folder
folders_to_process = data_folder.glob("*")

# Loop through folders to process
for path in folders_to_process:

    # If current path is a folder
    if path.is_dir():
        # Process files
        project_folder_path = path
        project = project_folder_path.name
        project_filepath = next(project_folder_path.glob(f"{project}.*"))
        groups_filepaths = list(project_folder_path.glob("*_g*.*"))
        abgrid_main = ABGridMain(project, project_folder_path, project_filepath, groups_filepaths)
        abgrid_main.generate_reports(args.language, args.with_sociogram)
        abgrid_main.generate_answer_sheets(args.language)