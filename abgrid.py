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
parser.add_argument("-g", "--groups", type=int, choices=range(1, 21), default=1,
                    help="Number of groups (1 to 20).")
parser.add_argument("-m", "--members_per_group", type=int, choices=range(6, 36), 
                    help="Number of members per group (6 to 35).")
parser.add_argument("-u", "--user", type=str, required=True, 
                    help="Username.")
parser.add_argument("-l", "--language", choices=LANGUAGES, default="en", 
                    help="Language used.")

# Parse the arguments
args = parser.parse_args()

try:

    # Setup the path to the project folder
    project_folderpath = Path("./data") / args.user / args.project

    # Handle init action
    if args.action == "init":

        # Make sure project folder does not already exist
        if project_folderpath.exists():
            raise FileExistsError(f"{args.project} already exists.")
        
        # If project folder can be created
        else:
            # Create project folder
            ABGridMain.init_project(project_folderpath, args.project, args.language)

    # Handle other actions (i.e., groups, answersheets, reports)
    else:
        # Find the project file within the project folder
        project_filepath = next(project_folderpath.glob(f"{args.project}.*"))

        # Determine how many group files were already created
        groups_filepaths = [ path for path in project_folderpath.glob("*_g*.*") if re.search(r"_g\d+\.yaml$", path.name) ]
        groups_already_created = len(groups_filepaths)
        
        # Determine how many group files to be created
        groups_to_create = range(groups_already_created +1, groups_already_created + args.groups +1)
        
        # Create an instance of ABGridMain 
        abgrid_main = ABGridMain(args.project, project_folderpath, project_filepath, groups_filepaths)
        
        # handle actions
        match args.action:
            
            case "groups":
                # Create group files
                abgrid_main.generate_group_inputs(groups_to_create, args.members_per_group, args.language)

            case "sheets":
                # Generate asnwershexets
                abgrid_main.generate_answer_sheets(args.language)
            
            case "reports":
                # Generate reports
                abgrid_main.generate_reports(args.language)

# Hande file already exists error
except FileExistsError as error:
    print(error)

# Handle cases where no project file is found
except StopIteration as error:
    print(error)

# Handle residual cases
except Exception as error:
    print(error)
