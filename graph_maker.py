import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import seaborn as sns
import inspect

from utils import get_child_folders


class BaseGraphMaker:
    STREAM_FILES_SUFFIX = "_streams_session.feather"
    EPOC_FILES_SUFFIX = "_epocs_data.feather"
    STREAM_FILES_DIRECTORY = "processed"
    EPOC_FILES_DIRECTORY = "extracted"

    def __init__(self, date_folder, should_save_graphs, should_show_graphs, meta_variable_name, meta_variable_type, meta_variable_unit, meta_variable_processor_function):
        self.date_folder = date_folder
        self.should_save_graphs = should_save_graphs
        self.should_show_graphs = should_show_graphs
        self.save_directory = (self.date_folder / ".." /
                               ".." / "graphs" / self.date_folder.name).resolve()
        self.meta_variable_name = meta_variable_name
        self.meta_variable_type = meta_variable_type
        self.meta_variable_unit = meta_variable_unit
        num_args_meta_variable_processor_function = len(
            inspect.signature(meta_variable_processor_function).parameters)
        if num_args_meta_variable_processor_function == 1:
            self.meta_variable_processor_function = meta_variable_processor_function
        elif num_args_meta_variable_processor_function == 3:
            self.meta_variable_processor_function = lambda filename: meta_variable_processor_function(
                filename, meta_variable_unit, meta_variable_type)
        else:
            raise ValueError(
                f"Expected num_args_meta_variable_processor_function to take 1 or 3 args, got {num_args_meta_variable_processor_function}")

    def extract_aligned(self, df, t0, t_window):
        t_rel = df['time'].to_numpy() - t0
        sig = df['delta_signal_poly_zscore'].to_numpy()
        return np.interp(t_window, t_rel, sig, left=np.nan, right=np.nan)

    def save_and_show_graph(self, save_file_name):
        if not self.save_directory.is_dir():
            self.save_directory.mkdir(parents=True)
            date_folder_name = self._date_folder_name()
            date_folder_name_str = f"[{date_folder_name}]" if date_folder_name else ""
            print(
                f"[+]{date_folder_name_str} Graph directory created:\n\t📊📂\t{self.save_directory}")
        if self.should_save_graphs:
            plt.savefig(self.save_directory / save_file_name)
        if self.should_show_graphs:
            plt.show()
        plt.cla()
        plt.clf()
        plt.close("all")

    def _date_folder_name(self):
        return self.date_folder.name


class SingleExperimentGraphMaker(BaseGraphMaker):
    def __init__(self, date_folder, mouse_experiment_name, should_save_graphs, should_show_graphs, meta_variable_name, meta_variable_type, meta_variable_unit, meta_variable_processor_function):
        BaseGraphMaker.__init__(
            self, date_folder, should_save_graphs, should_show_graphs, meta_variable_name, meta_variable_type, meta_variable_unit, meta_variable_processor_function)
        self.mouse_experiment_name = mouse_experiment_name
        self.mouse_data_directory = date_folder / self.mouse_experiment_name

    def get_data_dicts(self):
        return_data_dicts = []
        stream_files = list(self.mouse_data_directory.glob(
            f"{SingleExperimentGraphMaker.STREAM_FILES_DIRECTORY}/*{SingleExperimentGraphMaker.STREAM_FILES_SUFFIX}"))
        stream_files.sort(key=lambda file_path_object: self.meta_variable_processor_function(
            file_path_object.name))
        for stream_file_path in stream_files:
            stream_dataframe = pd.read_feather(stream_file_path)
            experiment_name = stream_file_path.name.replace(
                SingleExperimentGraphMaker.STREAM_FILES_SUFFIX, "")
            meta_variable_value = self.meta_variable_processor_function(
                experiment_name)
            epoc_file_path = self.mouse_data_directory / SingleExperimentGraphMaker.EPOC_FILES_DIRECTORY / \
                (experiment_name + SingleExperimentGraphMaker.EPOC_FILES_SUFFIX)
            epoc_dataframe = pd.read_feather(epoc_file_path)
            return_data_dicts.append(
                {
                    "experiment_name": experiment_name,
                    self.meta_variable_name: meta_variable_value,
                    "stream_dataframe": stream_dataframe,
                    "epoc_dataframe": epoc_dataframe
                }
            )
        return return_data_dicts

    def graph_z_score_over_time(self, data_dict):
        ax = data_dict["stream_dataframe"].plot(
            x="time", y="delta_signal_poly_zscore", figsize=(20, 5))
        ax.set_title(data_dict["experiment_name"])
        ax.set_xlabel('time')
        ax.set_ylabel('delta_signal_poly_zscore (offset)')
        ax.grid(True, alpha=0.3)
        self.save_and_show_graph(
            f"{self.mouse_experiment_name}_{data_dict[self.meta_variable_name]}{self.meta_variable_unit.lower()}_z_score_over_time")

    def graph_z_score_and_laser_bursts_over_time(self, data_dict):
        ax = data_dict["stream_dataframe"].plot(
            x="time",
            y="delta_signal_poly_zscore",
            figsize=(20, 5)
        )
        graph_title = f"{data_dict[self.meta_variable_name]} {self.meta_variable_unit}"
        ax.set_title(graph_title)
        ax.set_xlabel('time')
        ax.set_ylabel('delta_signal_poly_zscore (offset)')
        ax.grid(True, alpha=0.3)
        epoc_dataframe = data_dict["epoc_dataframe"]
        epocs = epoc_dataframe[epoc_dataframe['name'] == "PtC0"]
        number_of_pulses = 20
        burst_duration = number_of_pulses / data_dict[self.meta_variable_name]
        for _, row in epocs.iterrows():
            ax.axvspan(row['onset'], row['onset'] +
                       burst_duration, color='red', alpha=0.6)
        self.save_and_show_graph(
            f"{self.mouse_experiment_name}_{data_dict[self.meta_variable_name]}{self.meta_variable_unit.lower()}_z_score_and_laser_bursts_over_time")

    def graph_z_score_with_trials(self, data_dict):
        stream_dataframe = data_dict["stream_dataframe"]
        epoc_dataframe = data_dict["epoc_dataframe"]
        frequency = data_dict[self.meta_variable_name]
        epocs = epoc_dataframe[epoc_dataframe["name"] == "PtC0"]
        t_pre = 5.0
        t_post = 40
        dt = np.median(np.diff(stream_dataframe['time'].to_numpy()))
        t_window = np.arange(-t_pre, t_post, dt)
        R_trials = []
        for _, ev in epocs.iterrows():
            t0 = ev['onset']
            R_trials.append(self.extract_aligned(
                stream_dataframe, t0, t_window))
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
        graph_title = f"{frequency} {self.meta_variable_unit}"
        ax.set_title(graph_title)
        ax.legend(loc='upper right', frameon=False)
        sns.despine()
        plt.tight_layout()
        self.save_and_show_graph(
            f"{self.mouse_experiment_name}_{data_dict[self.meta_variable_name]}{self.meta_variable_unit.lower()}_z_score_with_trials")

    def graph_all_z_scores_overlaid(self, data_dicts):
        _, ax = plt.subplots(figsize=(3, 3))
        for i, data_dict in enumerate(data_dicts):
            color = f"C{i}"
            stream_dataframe = data_dict["stream_dataframe"]
            epoc_dataframe = data_dict["epoc_dataframe"]
            epocs = epoc_dataframe[epoc_dataframe["name"] == "PtC0"]
            t_pre = 5.0
            t_post = 40
            dt = np.median(np.diff(stream_dataframe['time'].to_numpy()))
            t_window = np.arange(-t_pre, t_post, dt)
            R_trials = []
            for _, ev in epocs.iterrows():
                t0 = ev['onset']
                R_trials.append(self.extract_aligned(
                    stream_dataframe, t0, t_window))
            R_trials = np.vstack(R_trials)
            R_mean = np.nanmean(R_trials, axis=0)
            R_sem = np.nanstd(R_trials, axis=0) / np.sqrt(R_trials.shape[0])
            ax.plot(t_window, R_mean,
                    label=f"{data_dict[self.meta_variable_name]} {self.meta_variable_unit}", color=color)
            ax.fill_between(t_window, R_mean - R_sem, R_mean + R_sem,
                            alpha=0.2, color=color)
        ax.axvline(0, color='k', linestyle='--', linewidth=1)
        ax.set_xlabel('Time from Opto Stim(s)')
        ax.set_ylabel('Z-score')
        ax.legend(loc='upper right', frameon=False)
        sns.despine()
        plt.tight_layout()
        self.save_and_show_graph(
            f"{self.mouse_experiment_name}_all_z_scores_overlaid")

    def make_all_graphs(self):
        data_dicts = self.get_data_dicts()
        for data_dict in data_dicts:
            self.graph_z_score_over_time(data_dict)
            self.graph_z_score_and_laser_bursts_over_time(data_dict)
            self.graph_z_score_with_trials(data_dict)
        self.graph_all_z_scores_overlaid(data_dicts)


class MultiExperimentGraphMaker(BaseGraphMaker):
    # Makes the graphs that show data from multiple mouse-experiments for a given day
    # This script assumes that the folder for each mouse-experiment follows the
    # following naming convention:
    #       <mouse_name>_<experiment_name>
    # There should only be ONE underscore in the folder name
    BAR_WIDTH = 0.25

    def __init__(self, date_folder, should_save_graphs, should_show_graphs, meta_variable_name, meta_variable_type, meta_variable_unit, meta_variable_processor_function):
        BaseGraphMaker.__init__(
            self, date_folder, should_save_graphs, should_show_graphs, meta_variable_name, meta_variable_type, meta_variable_unit, meta_variable_processor_function)
        self.mouse_experiment_names = [
            folder.name for folder in get_child_folders(self.date_folder)]
        self.mouse_experiments_dict = {}
        for mouse_experiment_name in self.mouse_experiment_names:
            mouse_name, experiment_name = mouse_experiment_name.split("_")
            if self.mouse_experiments_dict.get(mouse_name) is None:
                self.mouse_experiments_dict[mouse_name] = {}
            graph_maker = SingleExperimentGraphMaker(
                date_folder=self.date_folder,
                mouse_experiment_name=mouse_experiment_name,
                should_save_graphs=False,
                should_show_graphs=False,
                meta_variable_name=meta_variable_name,
                meta_variable_type=meta_variable_type,
                meta_variable_unit=meta_variable_unit,
                meta_variable_processor_function=meta_variable_processor_function)
            data_dicts = graph_maker.get_data_dicts()
            self.mouse_experiments_dict[mouse_name][experiment_name] = data_dicts
        self.calculate_amplitude_for_all_experiments()
        self.calculate_amplitude_means_and_sems_per_frequency()
        self.mouse_names = sorted(list(self.mouse_experiments_dict.keys()))
        self.log_name = "Multiple experiment"

    def calculate_amplitude_from_data_dict(self, data_dict):
        stream_dataframe = data_dict["stream_dataframe"]
        epoc_dataframe = data_dict["epoc_dataframe"]
        epocs = epoc_dataframe[epoc_dataframe["name"] == "PtC0"]
        t_pre = 5.0
        t_post = 20
        dt = np.median(np.diff(stream_dataframe['time'].to_numpy()))
        t_window = np.arange(-t_pre, t_post, dt)
        R_trials = []
        for _, ev in epocs.iterrows():
            t0 = ev['onset']  # align to onset
            R_trials.append(self.extract_aligned(
                stream_dataframe, t0, t_window))
        R_trials = np.vstack(R_trials)  # shape: n_trials x n_timepoints
        # mean across trials (ignore NaNs at edges if any)
        R_mean = np.nanmean(R_trials, axis=0)
        # optional: SEM
        R_sem = np.nanstd(R_trials, axis=0) / np.sqrt(R_trials.shape[0])
        # amplitude
        R_max = np.nanmax(R_trials)
        R_min = np.nanmin(R_trials)
        R_amp = np.abs(R_max - R_min)
        return R_amp

    def calculate_amplitude_for_all_experiments(self):
        for mouse_name, experiments_dict in self.mouse_experiments_dict.items():
            for experiment_name, data_dicts in experiments_dict.items():
                for data_dict in data_dicts:
                    data_dict["amplitude"] = self.calculate_amplitude_from_data_dict(
                        data_dict)

    def calculate_amplitude_means_and_sems_per_frequency(self):
        self.experiment_frequency_data_dict = {}
        for mouse_name, experiments_dict in self.mouse_experiments_dict.items():
            for experiment_name, data_dicts in experiments_dict.items():
                for data_dict in data_dicts:
                    amplitude = data_dict["amplitude"]
                    frequency = data_dict[self.meta_variable_name]
                    if self.experiment_frequency_data_dict.get(experiment_name) is None:
                        self.experiment_frequency_data_dict[experiment_name] = {
                        }
                    if self.experiment_frequency_data_dict[experiment_name].get(frequency) is None:
                        self.experiment_frequency_data_dict[experiment_name][frequency] = {
                            "amplitudes": {}
                        }
                    self.experiment_frequency_data_dict[experiment_name][
                        frequency]["amplitudes"][mouse_name] = amplitude
        for experiment_name, frequency_data_dict in self.experiment_frequency_data_dict.items():
            for frequency, data_dict in frequency_data_dict.items():
                data_dict["mean"] = np.mean(
                    list(data_dict["amplitudes"].values()))
                data_dict["sem"] = scipy.stats.sem(
                    list(data_dict["amplitudes"].values()))

    def _graph_bars(self, frequency_data_dict, x_positions, experiment_index, experiment_name):
        graph_offset = MultiExperimentGraphMaker.BAR_WIDTH * experiment_index
        for frequency, data_dict in frequency_data_dict.items():
            frequency_index = self.frequencies.index(frequency)
            white = 15
            color = white - 2 * experiment_index
            str_color = "#" + (f"{color:x}" * 3)
            plt.bar(
                x_positions[frequency_index] + graph_offset,
                data_dict["mean"],
                linewidth=1,
                label=f"{frequency} {self.meta_variable_unit}",
                yerr=data_dict["sem"],
                capsize=5,
                width=MultiExperimentGraphMaker.BAR_WIDTH,
                color=str_color,
                edgecolor='black')
            plt.text(x_positions[frequency_index] + graph_offset,
                     0.1,
                     experiment_name,
                     ha='center',
                     va='bottom',
                     color='black')

    def _graph_dots_and_lines(self, experiment_names, mouse_name):
        for frequency_index, frequency in enumerate(self.frequencies):
            x_values = []
            y_values = []
            for experiment_index, experiment_name in enumerate(experiment_names):
                graph_offset = MultiExperimentGraphMaker.BAR_WIDTH * experiment_index
                x_values.append(frequency_index +
                                graph_offset * experiment_index)
                y_value = self.experiment_frequency_data_dict[
                    experiment_name][frequency]["amplitudes"][mouse_name]
                y_values.append(y_value)
            plt.plot(
                x_values,
                y_values,
                marker='o',
                markersize=3,
                color=f"C{self.mouse_names.index(mouse_name)}"
            )

    def _get_tick_x_positions(self, x_positions, number_of_experiments):
        tick_x_positions = [
            x - MultiExperimentGraphMaker.BAR_WIDTH * 0.5 for x in x_positions]
        tick_x_positions = [x + MultiExperimentGraphMaker.BAR_WIDTH *
                            (number_of_experiments / 2) for x in tick_x_positions]
        return tick_x_positions

    def _generate_mouse_legend(self):
        handles = []
        for i, mouse in enumerate(self.mouse_names):
            mouse_line = plt.Line2D(
                [0], [0],
                marker='o',
                color=f"C{i}",
                markersize=3,
                label=mouse)
            handles.append(mouse_line)
        plt.legend(
            handles=handles,
            loc="upper right",
            bbox_to_anchor=(1.13, 1))

    def _gather_amplitudes_into_frequency_to_experiments_map(self):
        map_frequency_to_experiments = {}
        for experiment_name, frequency_data_dict in self.experiment_frequency_data_dict.items():
            for frequency in self.frequencies:
                data_dict = frequency_data_dict[frequency]
                amplitudes = [value for _,
                              value in data_dict["amplitudes"].items()]
                if map_frequency_to_experiments.get(frequency) is None:
                    map_frequency_to_experiments[frequency] = {}
                map_experiments_to_amplitudes = map_frequency_to_experiments[frequency]
                map_experiments_to_amplitudes[experiment_name] = amplitudes
        return map_frequency_to_experiments

    def _get_graph_string_from_p_value(self, p_value):
        if p_value < 0.001:
            graph_string = '***'
        elif p_value < 0.01:
            graph_string = '**'
        elif p_value < 0.05:
            graph_string = '*'
        else:
            graph_string = ''
        return graph_string

    def _generate_stats(self):
        map_frequency_to_experiments = self._gather_amplitudes_into_frequency_to_experiments_map()
        text_x_positions = self._get_tick_x_positions(
            self.x_positions, len(self.experiment_names))
        print(
            f"[+][{self.date_folder.name}] T-stats and P-values across all experiments:")
        for frequency, map_experiment_to_amplitudes in map_frequency_to_experiments.items():
            amplitude_lists = list(map_experiment_to_amplitudes.values())
            t_stat, p_value = scipy.stats.ttest_ind(*amplitude_lists)
            print(
                f"\t{frequency}{self.meta_variable_unit}:\tt_stat: {t_stat:.5f}\tp_value: {p_value:.5f}")
            graph_string = self._get_graph_string_from_p_value(p_value)
            frequency_index = self.frequencies.index(frequency)
            plt.text(
                text_x_positions[frequency_index],
                9,
                graph_string,
                ha='center',
                va='bottom',
                color='black')

    def graph_all_z_score_differences_across_frequency(self):
        plt.figure(figsize=(8, 4))
        self.x_positions = [0, 1, 2]
        self.frequencies = [5, 10, 20]
        self.experiment_names = list(
            self.experiment_frequency_data_dict.keys())
        for experiment_name in self.experiment_names:
            frequency_data_dict = self.experiment_frequency_data_dict[experiment_name]
            experiment_index = self.experiment_names.index(experiment_name)
            self._graph_bars(frequency_data_dict, self.x_positions,
                             experiment_index, experiment_name)
        for mouse_name in self.mouse_names:
            self._graph_dots_and_lines(self.experiment_names, mouse_name)
        plt.xlabel(
            f'{self.meta_variable_name.capitalize()} ({self.meta_variable_unit})', fontsize=12)
        plt.ylabel('Z-score difference', fontsize=12)
        plt.ylim(0, 10)
        # plt.title(f"{self.date_folder.name}", fontsize=12)
        plt.xticks(
            self._get_tick_x_positions(
                self.x_positions, len(self.experiment_names)),
            self.frequencies)
        self._generate_mouse_legend()
        self._generate_stats()
        sns.despine()
        self.save_and_show_graph(
            f"{self.date_folder.name}_amplitude_comparison_across_frequencies")

    def make_all_graphs(self):
        self.graph_all_z_score_differences_across_frequency()
