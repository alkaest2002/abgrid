import argparse
from pathlib import Path
from lib.abgrid_main import ABGridMain

# Set up the argument parser
parser = argparse.ArgumentParser(prog="ABGrid")

# Define expected command-line arguments
parser.add_argument("-a", "--action", required=True, choices=["init", "sheets", "reports"], 
                    help="Action to perform: 'init', 'sheets', or 'reports'.")
parser.add_argument("-p", "--project", required=True, 
                    help="Name of the project.")
parser.add_argument("-g", "--groups", type=int, choices=range(1, 21), 
                    help="Number of groups (1 to 20).")
parser.add_argument("-m", "--members_per_group", type=int, choices=range(3, 16), 
                    help="Number of members per group (3 to 15).")

# Parse the arguments
args = parser.parse_args()

# Handle the 'init' action
if args.action == "init":
    # Check if both groups and members per group arguments are provided
    if not all([args.groups, args.members_per_group]):
        # Display a message if any required argument is missing
        print("Please specify the following parameters: project's name (-p), number of groups (-g), number of members per group (-m)")
    else:
        # Initialize the project with specified parameters
        ABGridMain.init_project(args.project, args.groups, args.members_per_group)
else:    
    try:
        # Setup the path to the project folder
        project_folder_path = Path("./data") / args.project
        
        # Check if the project folder exists
        if not project_folder_path.exists():
            # Raise an error if the project folder does not exist
            raise FileNotFoundError(f"The project folder ({project_folder_path.name}) does not exist")
        
        # Find the project file within the project folder
        project_filepath = next(project_folder_path.glob(f"{args.project}.*"))
        
        # Find all group files, ensuring at least one exists
        if len(groups_filepaths := list(project_folder_path.glob("*gruppo_*.*"))) == 0:
             raise FileNotFoundError(f"The project folder ({project_folder_path.name}) does not contain any group files")

        # Create an instance of ABGridMain with project details
        abgrid_main = ABGridMain(args.project, project_folder_path, project_filepath, groups_filepaths)
        
        # Handle 'sheets' and 'reports' action
        if args.action == "sheets":
            # Generate answer sheets
            abgrid_main.generate_answer_sheets()
        else:
            # Generate reports
            abgrid_main.generate_reports()

    # Handle file not found errors
    except FileNotFoundError as error:
        print(error)
    
    # Handle cases where no project file is found
    except StopIteration as error:
        print(error)
