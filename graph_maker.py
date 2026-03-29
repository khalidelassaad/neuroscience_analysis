import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

"""
This code takes as inputs: 
    `data_directory`
    `mouse`

This code expects the following file structure:

📂 `data_directory`/        # directory containing data of all the mice
+-- 📂 `mouse`/             # directory containing data of a specific mouse
    +-- 📂 `processed`/     # directory containing mouse's processed data
    +-- 📂🆕 `graphs`/      # NEW: directory will be created, containing mouse's graphs
"""

class GraphMaker:
    # One instance per mouse
    STREAM_FILES_SUFFIX = "_streams_session.feather"
    EPOC_FILES_SUFFIX = "_epocs_data.feather"
    STREAM_FILES_DIRECTORY = "processed"
    EPOC_FILES_DIRECTORY = "extracted"

    def __init__(self, data_directory, mouse_experiment_name, should_save_graphs, should_show_graphs):
        self.mouse_experiment_name = mouse_experiment_name
        self.mouse_data_directory = data_directory / self.mouse_experiment_name
        self.should_save_graphs = should_save_graphs
        self.should_show_graphs = should_show_graphs
        self.save_directory = self.mouse_data_directory / "graphs"

    def extract_aligned(self, df, t0, t_window):
        t_rel = df['time'].to_numpy() - t0
        sig   = df['delta_signal_poly_zscore'].to_numpy()
        return np.interp(t_window, t_rel, sig, left=np.nan, right=np.nan)

    def get_frequency_from_experiment_name(self, filename):
        split_filename_list = filename.split("_")
        for file_name_part in split_filename_list:
            if "hz" not in file_name_part.lower():
                continue
            frequency_string = file_name_part[:-2]
            return int(frequency_string)

    def get_data_dicts(self):
        return_data_dicts = []
        stream_files = list(self.mouse_data_directory.glob(f"{GraphMaker.STREAM_FILES_DIRECTORY}/*{GraphMaker.STREAM_FILES_SUFFIX}"))
        stream_files.sort(key = lambda file_path_object : self.get_frequency_from_experiment_name(file_path_object.name))
        for stream_file_path in stream_files:
            stream_dataframe = pd.read_feather(stream_file_path)
            experiment_name = stream_file_path.name.replace(GraphMaker.STREAM_FILES_SUFFIX, "")
            frequency = self.get_frequency_from_experiment_name(experiment_name)
            epoc_file_path = self.mouse_data_directory / GraphMaker.EPOC_FILES_DIRECTORY / (experiment_name + GraphMaker.EPOC_FILES_SUFFIX)
            epoc_dataframe = pd.read_feather(epoc_file_path)
            return_data_dicts.append(
                {
                    "experiment_name": experiment_name, 
                    "frequency": frequency,
                    "stream_dataframe": stream_dataframe,
                    "epoc_dataframe": epoc_dataframe
                }
            ) 
        return return_data_dicts

    def save_and_show_graph(self, save_file_name):
        if not self.save_directory.is_dir():
            self.save_directory.mkdir()
            print(f"[+][{self.mouse_experiment_name}] Directory made: {self.save_directory}")
        if self.should_save_graphs:
            graph_path = self.save_directory / save_file_name
            plt.savefig(graph_path)
            print(f"[+][{self.mouse_experiment_name}] Graph saved: {graph_path}.png")
        if self.should_show_graphs:
            plt.show()

    def graph_z_score_over_time(self, data_dict):
        ax = data_dict["stream_dataframe"].plot(x="time", y="delta_signal_poly_zscore", figsize=(20, 5))
        ax.set_title(data_dict["experiment_name"])
        ax.set_xlabel('time')
        ax.set_ylabel('delta_signal_poly_zscore (offset)')
        ax.grid(True, alpha=0.3)
        self.save_and_show_graph(f"{self.mouse_experiment_name}_{data_dict["frequency"]}hz_z_score_over_time")

    def graph_z_score_and_laser_bursts_over_time(self, data_dict):
        ax = data_dict["stream_dataframe"].plot(
            x="time", 
            y="delta_signal_poly_zscore", 
            figsize=(20, 5)
        )
        graph_title = f"{data_dict["frequency"]} Hz"
        ax.set_title(graph_title)
        ax.set_xlabel('time')
        ax.set_ylabel('delta_signal_poly_zscore (offset)')
        ax.grid(True, alpha=0.3)
        epoc_dataframe = data_dict["epoc_dataframe"]
        epocs = epoc_dataframe[epoc_dataframe['name'] == "PtC0"]
        number_of_pulses = 20
        burst_duration = number_of_pulses / data_dict["frequency"]
        for _, row in epocs.iterrows():
            ax.axvspan(row['onset'], row['onset'] + burst_duration, color='red', alpha=0.6)
        self.save_and_show_graph(f"{self.mouse_experiment_name}_{data_dict["frequency"]}hz_z_score_and_laser_bursts_over_time")

    def graph_z_score_with_trials(self, data_dict):
        stream_dataframe = data_dict["stream_dataframe"]
        epoc_dataframe = data_dict["epoc_dataframe"]
        frequency = data_dict["frequency"]
        epocs = epoc_dataframe[epoc_dataframe["name"] == "PtC0"]
        t_pre  = 5.0
        t_post = 40
        dt = np.median(np.diff(stream_dataframe['time'].to_numpy()))
        t_window = np.arange(-t_pre, t_post, dt)
        R_trials = []
        for _, ev in epocs.iterrows():
            t0 = ev['onset']
            R_trials.append(self.extract_aligned(stream_dataframe, t0, t_window))
        R_trials = np.vstack(R_trials)
        R_mean = np.nanmean(R_trials, axis=0)
        R_sem = np.nanstd(R_trials, axis=0) / np.sqrt(R_trials.shape[0])
        _, ax = plt.subplots(figsize=(3, 3))
        ax.plot(t_window, R_mean, label='stimulated DA', color='#D32F2F')
        ax.fill_between(t_window, R_mean - R_sem, R_mean + R_sem,
                        alpha=0.2, color='#D32F2F')
        ax.axvline(0, color='k', linestyle='--', linewidth=1)
        ax.set_xlabel('Time from Opto Stim(s)')
        ax.set_ylabel('Z-score')
        graph_title = f"{frequency} Hz"
        ax.set_title(graph_title)
        ax.legend(loc='upper right',frameon=False)
        sns.despine()
        plt.tight_layout()
        self.save_and_show_graph(f"{self.mouse_experiment_name}_{data_dict["frequency"]}hz_z_score_with_trials")

    def graph_all_z_scores_overlaid(self, data_dicts):
        _, ax = plt.subplots(figsize=(3, 3))
        colors = ['#377eb8', '#ff7f00', '#4daf4a']
        for i, data_dict in enumerate(data_dicts):
            stream_dataframe = data_dict["stream_dataframe"]
            epoc_dataframe = data_dict["epoc_dataframe"]
            epocs = epoc_dataframe[epoc_dataframe["name"] == "PtC0"]
            t_pre  = 5.0
            t_post = 40
            dt = np.median(np.diff(stream_dataframe['time'].to_numpy()))
            t_window = np.arange(-t_pre, t_post, dt)
            R_trials = []
            for _, ev in epocs.iterrows():
                t0 = ev['onset']
                R_trials.append(self.extract_aligned(stream_dataframe, t0, t_window))
            R_trials = np.vstack(R_trials)
            R_mean = np.nanmean(R_trials, axis=0)
            R_sem = np.nanstd(R_trials, axis=0) / np.sqrt(R_trials.shape[0])
            ax.plot(t_window, R_mean, label=f"{data_dict["frequency"]} Hz", color=colors[i])
            ax.fill_between(t_window, R_mean - R_sem, R_mean + R_sem,
                            alpha=0.2, color=colors[i])
        ax.axvline(0, color='k', linestyle='--', linewidth=1)
        ax.set_xlabel('Time from Opto Stim(s)')
        ax.set_ylabel('Z-score')
        ax.legend(loc='upper right', frameon=False)
        sns.despine()
        plt.tight_layout()
        self.save_and_show_graph(f"{self.mouse_experiment_name}_all_z_scores_overlaid")

    def make_all_graphs(self):
        data_dicts = self.get_data_dicts()
        for data_dict in data_dicts:
            self.graph_z_score_over_time(data_dict)
            self.graph_z_score_and_laser_bursts_over_time(data_dict)
            self.graph_z_score_with_trials(data_dict)
        self.graph_all_z_scores_overlaid(data_dicts)


if __name__ == "__main__":
    graph_maker = GraphMaker(
        data_directory=Path(f"/home/khalid/Downloads/path/frequency_data"),
        mouse_experiment_name="5741L",
        should_save_graphs=True,
        should_show_graphs=False
    )
    graph_maker.make_all_graphs()