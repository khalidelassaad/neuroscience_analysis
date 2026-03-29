import functions.tdt_analysis
import functions.py_fp
from pathlib import Path
from single_experiment_graph_maker import SingleExperimentGraphMaker
from dir_utils import HiddenPrints


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


class DataToGraphPipeline:
    def __init__(self, data_directory, mouse_experiment_name, log_file_name, should_save_graphs, should_show_graphs):
        self.mouse_experiment_name = mouse_experiment_name
        self.mouse_data_directory = data_directory / self.mouse_experiment_name
        self.log_file_path = self.mouse_data_directory / log_file_name
        self.raw_directory = self.mouse_data_directory / "raw"
        self.extracted_directory = self.mouse_data_directory / "extracted"
        self.processed_directory = self.mouse_data_directory / "processed"
        self.should_save_graphs = should_save_graphs
        self.should_show_graphs = should_show_graphs
        self.single_mouse_experiment_graph_maker = SingleExperimentGraphMaker(
            data_directory=data_directory,
            mouse_experiment_name=mouse_experiment_name,
            should_save_graphs=should_save_graphs,
            should_show_graphs=should_show_graphs)

    def raw_to_extracted(self):
        if not self.raw_directory.is_dir():
            raise FileNotFoundError(
                f"{self.raw_directory} should exist but does not.")
        if not self.extracted_directory.is_dir():
            self.extracted_directory.mkdir()
            print(
                f"[+][{self.mouse_experiment_name}] Directory created: {self.extracted_directory}")
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
                f"[+][{self.mouse_experiment_name}] Directory created: {self.processed_directory}")
        functions.tdt_analysis.main(
            str(self.extracted_directory),
            str(self.processed_directory),
            str(self.log_file_path)
        )

    def processed_to_graphs(self):
        self.single_mouse_experiment_graph_maker.make_all_graphs()

    def run(self):
        self.raw_to_extracted()
        print(
            f"[+][{self.mouse_experiment_name}] Data processing step completed: raw -> extracted")
        self.extracted_to_processed()
        print(
            f"[+][{self.mouse_experiment_name}] Data processing step completed: extracted -> processed")
        self.processed_to_graphs()
        print(
            f"[+][{self.mouse_experiment_name}] All graphs successfully created!")
        print(f"[+][{self.mouse_experiment_name}] ✨📊 Enjoy your graphs! 📊✨")
        print(f"[+][{self.mouse_experiment_name}] Graph Directory: {self.single_mouse_experiment_graph_maker.save_directory}")


if __name__ == "__main__":
    data_to_graph_pipeline = DataToGraphPipeline(
        data_directory=Path(
            f"/home/khalid/Downloads/path/frequency_data/03242026"),
        mouse_experiment_name="4022L_ipV",
        log_file_name="log_4022L_ipV.csv",
        should_save_graphs=True,
        should_show_graphs=True)
    data_to_graph_pipeline.run()
