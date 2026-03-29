from pathlib import Path
from dir_utils import get_child_folders

class DateLevelGraphMaker:
    def __init__(self, date_folder, subject_prefix):
        self.date_folder = date_folder
        self.subject_prefix = subject_prefix
        self.mouse_experiment_names = [folder.name for folder in get_child_folders(self.date_folder)]

if __name__ == "__main__":
    DateLevelGraphMaker(
        date_folder=Path(f"/Users/cerahassinan/Downloads/nape_tidy_photom_tools-main/path/frequency_data/03192026"),
        subject_prefix="DATNAC"
    )