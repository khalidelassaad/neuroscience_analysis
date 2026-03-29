from datetime import datetime
from pathlib import Path
from graph_maker import MultiExperimentGraphMaker, SingleExperimentGraphMaker
from data_processor import DataProcessor
from utils import get_child_folders

CSV_HEADER_STRING = "experiment,subject,date,procedure,blockname,include,exclude_note,PC0,PC1,PC2,PC3,PC4,PC5,PC6,PC7,multi_config,fiber_id01,fiber_id02,blockname_multi_subject,trim_time_start,trim_time_end,signal_id01,signal_id02,control_id,sensor01,sensor02,smoothing_window,poly_degree_fitted_control,poly_degree_polyfit,down_sampled_freq,peth_pre,peth_post,events_of_interest,n_remove_first_events,n_remove_last_events,events_manual_fn\n"
CSV_ROW_TEMPLATE_STRING = "VTAstimNAC,{},{},dopamine,{},1,NA,laser_onset,NA,NA,NA,NA,NA,NA,NA,NA,nacsh_med,NA,NA,20,NA,465,NA,405,grabda_2m,NA,0.1,3,4,20,10,20,laser_onset,0,0,NA\n"


class DateFolderMultiExperimentProcessor:
    def __init__(self, date_folder, subject_prefix):
        self.date_folder = date_folder
        self.subject_prefix = subject_prefix

    def generate_csv_row(self, mouse_experiment_path, raw_experiment_path):
        blockname = raw_experiment_path.name
        blockname_parts = blockname.split("_")
        date_string = blockname_parts[0]
        date_object = datetime.strptime(date_string, "%m%d%Y")
        csv_date_string = datetime.strftime(date_object, "%-m/%-d/%y")
        mouse_experiment = mouse_experiment_path.name
        subject = f"{self.subject_prefix}_{mouse_experiment}"
        csv_row = CSV_ROW_TEMPLATE_STRING.format(
            subject, csv_date_string, blockname)
        return csv_row

    def generate_csv(self, mouse_experiment_path, raw_data_path):
        csv_rows = [CSV_HEADER_STRING]
        for raw_experiment_path in get_child_folders(raw_data_path):
            csv_row = self.generate_csv_row(
                mouse_experiment_path, raw_experiment_path)
            csv_rows.append(csv_row)
        csv_path = mouse_experiment_path / \
            f"log_{mouse_experiment_path.name}.csv"
        with open(csv_path, "w") as csv_file:
            csv_file.writelines(csv_rows)
        print(
            f"[+][{self.date_folder.name}][{mouse_experiment_path.name}] Log file created:\t{csv_path}")
        return csv_path

    def process_data_for_single_experiment(self, mouse_experiment_name, log_file_path):
        data_processor = DataProcessor(
            date_folder=self.date_folder,
            mouse_experiment_name=mouse_experiment_name,
            log_file_name=log_file_path)
        data_processor.run()

    def process_data_for_all_experiments(self):
        for mouse_experiment_path in get_child_folders(self.date_folder):
            raw_data_path = mouse_experiment_path / "raw"
            csv_path = self.generate_csv(mouse_experiment_path, raw_data_path)
            self.process_data_for_single_experiment(
                mouse_experiment_path.name, csv_path)

    def make_all_graphs(self):
        for mouse_experiment_path in get_child_folders(self.date_folder):
            single_experiment_graph_maker = SingleExperimentGraphMaker(
                date_folder=self.date_folder,
                mouse_experiment_name=mouse_experiment_path.name,
                should_save_graphs=True,
                should_show_graphs=False)
            single_experiment_graph_maker.make_all_graphs()
        multi_experiment_graph_maker = MultiExperimentGraphMaker(
            date_folder=self.date_folder,
            should_save_graphs=True,
            should_show_graphs=False)
        multi_experiment_graph_maker.make_all_graphs()

    def process_and_graph_data(self):
        self.process_data_for_all_experiments()
        self.make_all_graphs()


if __name__ == "__main__":
    DateFolderMultiExperimentProcessor(
        date_folder=Path(
            f"/Users/khalid/neuroscience_analysis/experiment_data/03242026"),
        subject_prefix="DATNAC").process_and_graph_data()
