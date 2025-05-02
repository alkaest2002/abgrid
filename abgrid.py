import argparse
from pathlib import Path
from lib.abgrid_main import ABGridMain

parser = argparse.ArgumentParser(prog="ABGrid")
parser.add_argument("-a", "--action", required=True, choices=["init", "sheets", "reports"])
parser.add_argument("-p", "--project", required=True,)
parser.add_argument("-g", "--groups", type=int, choices=range(1, 21))
parser.add_argument("-m", "--members_per_group", type=int, choices=range(3, 16))
args = parser.parse_args()

if args.action == "init":
    if not all([args.groups, args.members_per_group]):
        print("Please specify the following parameters: project's name (-p), number of groups (-g), number of members per group (-m)")
    else:
        ABGridMain.init_project(args.project, args.groups, args.members_per_group)
else:    
    try:
        project_folder_path = Path("./data") / args.project
        if not project_folder_path.exists():
            raise FileNotFoundError(f"The progect folder ({project_folder_path.name}) does not exists")
        
        project_filepath = next(project_folder_path.glob(f"{args.project}.*"))
        
        if len(groups_filepaths := list(project_folder_path.glob("*gruppo_*.*"))) == 0:
             raise FileNotFoundError(f"The progect folder ({project_folder_path.name}) does not exists")

        abgrid_main = ABGridMain(args.project, project_folder_path, project_filepath, groups_filepaths)
        
        if args.action == "sheets":
            abgrid_main.generate_answer_sheets()
        else:
            abgrid_main.generate_reports()

    except FileNotFoundError as error:
        print(error)
    
    except StopIteration as error:
        print(error)
    