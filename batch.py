from pathlib import Path
from lib.abgrid_main import ABGridMain

data_folder = Path("./data")
folders = data_folder.glob("*")

for folder in folders:
    if folder.is_dir():
        project = folder.name
        project_folder_path = data_folder / project
        print(project_folder_path)
        project_filepath = next(project_folder_path.glob(f"{project}.*"))
        groups_filepaths = list(project_folder_path.glob("*gruppo_*.*"))
        abgrid_main = ABGridMain(project, project_folder_path, project_filepath, groups_filepaths)
        abgrid_main.generate_reports()