import re
import argparse
from pathlib import Path
from lib.abgrid_main import ABGridMain

# Available languages
LANGUAGES = ["en", "it"]

# Set up the argument parser
parser = argparse.ArgumentParser(prog="ABGrid")

# Define expected command-line arguments
parser.add_argument("-a", "--action", required=True, choices=["init", "groups", "sheets", "reports"], 
                    help="Action to perform: 'init', 'groups', 'sheets', or 'reports'.")
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

# Parse arguments
args = parser.parse_args()

# catch errors
try:

    # Setup the path to the project folder
    project_folderpath = Path("./data") / args.user / args.project

    # Handle init action
    if args.action == "init":

        # Make sure project folder does not already exist
        if project_folderpath.exists():
            raise FileExistsError(f"{args.project} already exists.")
        
        # If project folder does not exists
        else:
            
            # Create project folder
            ABGridMain.init_project(args.project, project_folderpath, args.language)

    # Handle other actions (i.e., groups, sheets, reports)
    else:
        
        # Find the project file within the project folder
        project_filepath = next(project_folderpath.glob(f"{args.project}.*"))

        # Determine how many group files are already created
        groups_filepaths = [ path for path in project_folderpath.glob("*_g*.*") if re.search(r"_g\d+\.\w+$", path.name) ]
        groups_already_created = len(groups_filepaths)
        
        # Determine how many group files to be created
        groups_to_create = range(groups_already_created +1, groups_already_created + args.groups +1)
        
        # Create an instance of ABGridMain 
        abgrid_main = ABGridMain(args.project, project_folderpath, project_filepath, groups_filepaths)
        
        # handle actions
        match args.action:
            
            case "groups":
                # Generate group files
                abgrid_main.generate_group_inputs(groups_to_create, args.members_per_group, args.language)

            case "sheets":
                # Generate answersheets
                abgrid_main.generate_answer_sheets(args.language)
            
            case "reports":
                # Generate reports
                abgrid_main.generate_reports(args.language, args.with_sociogram)

# File already exists error
except FileExistsError as error:
    print(error)

# No project file is found
except StopIteration as error:
    print(error)

# Residual cases
except Exception as error:
    print(error)
