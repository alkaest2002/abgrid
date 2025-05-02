import argparse
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
    abgrid_main = ABGridMain(args.project)
    if abgrid_main.abgrid_data:
        abgrid_main.generate_answer_sheets() if args.action == "sheets" else  abgrid_main.generate_reports()