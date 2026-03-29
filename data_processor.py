import functions.tdt_analysis
import functions.py_fp
from utils import HiddenPrints


"""
This code takes as inputs: 
    `data_directory`
    `mouse`
    `log_file_name`

This code expects the following file structure:

📂 `data_directory`/        # directory containing data of all the mice
+-- 📂 `mouse`/             # directory containing data of a specific mouse
    +-- 📄 `log_file_name`      # .csv file containing log data needed for extracted->processed step
    +-- 📂 `raw`/           # directory containing that mouse's raw data
    +-- 📂🆕 `extracted`/   # NEW: directory will be created, containing mouse's extracted data
    +-- 📂🆕 `processed`/   # NEW: directory will be created, containing mouse's processed data
    +-- 📂🆕 `graphs`/      # NEW: directory will be created, containing mouse's graphs
"""


class DataProcessor:
    def __init__(self, date_folder, mouse_experiment_name, log_file_name):
        self.mouse_experiment_name = mouse_experiment_name
        self.date_folder = date_folder
        self.mouse_data_directory = date_folder / self.mouse_experiment_name
        self.log_file_path = self.mouse_data_directory / log_file_name
        self.raw_directory = self.mouse_data_directory / "raw"
        self.extracted_directory = self.mouse_data_directory / "extracted"
        self.processed_directory = self.mouse_data_directory / "processed"

    def raw_to_extracted(self):
        if not self.raw_directory.is_dir():
            raise FileNotFoundError(
                f"{self.raw_directory} should exist but does not.")
        if not self.extracted_directory.is_dir():
            self.extracted_directory.mkdir()
            print(
                f"[+][{self.date_folder.name}][{self.mouse_experiment_name}] Directory created: {self.extracted_directory}")
        with HiddenPrints():
            functions.py_fp.tidy_tdt_extract_and_tidy(
                str(self.raw_directory),
                str(self.extracted_directory),
                ['405A', '465A'])

    def extracted_to_processed(self):
        if not self.extracted_directory.is_dir():
            raise FileNotFoundError(
                f"{self.extracted_directory} should exist but does not.")
        if not self.processed_directory.is_dir():
            self.processed_directory.mkdir()
            print(
                f"[+][{self.date_folder.name}][{self.mouse_experiment_name}] Directory created: {self.processed_directory}")
        functions.tdt_analysis.main(
            str(self.extracted_directory),
            str(self.processed_directory),
            str(self.log_file_path)
        )

    def run(self):
        self.raw_to_extracted()
        self.extracted_to_processed()
