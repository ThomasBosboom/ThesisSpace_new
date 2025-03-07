# Standard
import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Define path to import src files
file_name = os.path.splitext(os.path.basename(__file__))[0]
file_directory = os.path.realpath(__file__)
for _ in range(5):
    file_directory = os.path.dirname(file_directory)
    sys.path.append(file_directory)

# # Define current time
# current_time = datetime.now().strftime("%Y%m%d%H%M")

from tests.postprocessing import TableGenerator, ProcessNavigationResults
from tests.analysis import helper_functions
from tests import utils

class ProcessOptimizationResults():

    def __init__(self, time_tag, optimization_model, save_settings={"save_table": True, "save_figure": False, "current_time": float, "file_name": str}, **kwargs):

        for key, value in save_settings.items():
            if save_settings["save_table"] or save_settings["save_figure"]:
                setattr(self, key, value)

        self.time_tag = str(time_tag)
        self.optimization_model = optimization_model
        self.optimization_results = self.optimization_model.load_from_json(time_tag, folder_name=self.file_name)
        self.color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']


    def plot_iteration_history(self, show_design_variables=True, compare_time_tags={}, highlight_mean_only=True, show_annual=False):

        # Initialize the plots
        if show_design_variables:
            fig, axs = plt.subplots(3, 1, figsize=(8, 7.5), sharex=True)
        else:
            fig, axs = plt.subplots(2, 1, figsize=(8, 4), sharex=True)

        optimization_keys = self.optimization_results["file_name"]
        time_tags = {optimization_keys: [self.optimization_results["current_time"]]}
        initial_design_vector = self.optimization_results["initial_design_vector"]

        if compare_time_tags:
            time_tags = compare_time_tags

        # Collect optimization results
        optimization_results_dict = {}
        for label, time_tags_list in time_tags.items():
            optimization_results_dict[label] = {}
            for time_tag in time_tags_list:
                file_name = self.file_name
                if label != self.optimization_results["file_name"]:
                    if "nelder_mead" in label or "Nelder-Mead" in label or "Nelder Mead" in label:
                        file_name = "optimization_analysis_nelder_mead"
                    elif "particle_swarm" in label or "Particle-Swarm" in label or "Particle Swarm" in label:
                        file_name = "optimization_analysis_particle_swarm"

                optimization_results_dict[label][time_tag] = self.optimization_model.load_from_json(time_tag, folder_name=file_name)

        # Generate statistics of iteration histories
        for index, (label, optimization_results) in enumerate(optimization_results_dict.items()):

            # Plotting settings
            marker = None
            alpha = 1
            color = self.color_cycle[int(index % 10)]
            if highlight_mean_only:
                # color = "lightgray"
                alpha = 0.2
                # label = None

            iterations = {}
            design_vectors = {}
            objective_values = {}
            objective_values_annual = {}
            reduction = {}
            for time_tag, optimization_result in optimization_results.items():

                # Extract from iteration histories
                iterations[time_tag] = []
                design_vectors[time_tag] = []
                objective_values[time_tag] = []
                objective_values_annual[time_tag] = []
                reduction[time_tag] = []
                for iteration, iteration_data in optimization_result["iteration_history"].items():

                    iterations[time_tag].append(iteration)
                    design_vectors[time_tag].append(iteration_data["design_vector"])
                    objective_values[time_tag].append(iteration_data["objective_value"])
                    objective_values_annual[time_tag].append(iteration_data["objective_value_annual"])
                    reduction[time_tag].append(iteration_data["reduction"])

                # Plot the individual runs

                if show_annual:
                    axs[0].plot(iterations[time_tag], objective_values_annual[time_tag], marker=marker, label=None, alpha=alpha, color=color)
                else:
                    axs[0].plot(iterations[time_tag], objective_values[time_tag], marker=marker, label=None, alpha=alpha, color=color)
                axs[1].plot(iterations[time_tag], reduction[time_tag], marker=marker, label=None, alpha=alpha, color=color)


            iterations = list(iterations.values())
            design_vectors = list(design_vectors.values())
            objective_values = list(objective_values.values())
            objective_values_annual = list(objective_values_annual.values())
            reduction = list(reduction.values())

            # Calculate statistics over time tags per label
            means, stds = [], []
            for data in [objective_values, objective_values_annual, reduction]:

                # Determine the number of columns
                max_length = max(len(row) for row in data)

                # Create an empty array filled with np.nan
                array = np.full((len(data), max_length), np.nan)

                # Populate the array with the data
                for i, row in enumerate(data):
                    array[i, :len(row)] = row

                # Calculate the mean along the columns, ignoring nan values
                means.append(np.nanmean(array, axis=0))
                stds.append(np.nanstd(array, axis=0))

            if show_annual:
                axs[0].plot(range(0, max_length), means[1], marker=marker, label=label, alpha=1, color=color)
            else:
                axs[0].plot(range(0, max_length), means[0], marker=marker, label=label, alpha=1, color=color)
            axs[1].plot(range(0, max_length), means[2], marker=marker, label=label, alpha=1, color=color)


        axs[0].legend()
        axs[0].set_ylabel(r"||$\Delta V$|| [m/s]")
        axs[0].grid(alpha=0.5, linestyle='--', which='both')

        axs[1].legend()
        axs[1].set_ylabel("Reduction [%]")
        axs[1].grid(alpha=0.5, linestyle='--', which='both')

        if show_design_variables:
            design_vectors = np.array(design_vectors)[0, :, :]
            ncol = min(len(initial_design_vector), 7)
            for i in range(design_vectors.shape[1]):
                ls = "-"
                label = f'$T_{{{i + 1}}}$'
                if i >= ncol:
                    ls = "--"
                axs[2].plot(max(iterations, key=len), design_vectors[:, i], marker=marker, ls=ls, label=label)
            axs[2].set_xlabel('Iteration')
            axs[2].set_ylabel("Design variables [days]")
            axs[2].grid(alpha=0.5, linestyle='--', which='both')
            axs[2].xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

            axs[2].legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=ncol, fontsize="small", title="Design variables")
            # axs[2].legend(loc='best')
        else:
            axs[1].xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            axs[1].set_xlabel('Iteration')

        plt.tight_layout()

        if self.save_figure:
            if not compare_time_tags:
                utils.save_figure_to_folder(figs=[fig], labels=[f"{self.current_time}_iteration_history"], custom_sub_folder_name=self.file_name)
            if compare_time_tags:
                if len(compare_time_tags) >= 2:
                    utils.save_figure_to_folder(figs=[fig], labels=[f"comparison_iteration_history"], custom_sub_folder_name=self.file_name)
                else:
                    utils.save_figure_to_folder(figs=[fig], labels=[f"combined_iteration_history"], custom_sub_folder_name=self.file_name)


    def plot_optimization_result_comparisons(self, auxilary_settings, show_observation_window_settings=False, custom_num_runs=None):

        num_runs = self.optimization_results["num_runs"]
        if custom_num_runs is not None:
            num_runs = custom_num_runs

        observation_windows_settings = {
            "Default": [
                (self.optimization_results["initial_observation_windows"], num_runs, None),
            ],
            "Optimized": [
                (self.optimization_results["best_observation_windows"], num_runs, None)
            ],
        }

        if show_observation_window_settings:
            print("Observation window settings \n:", observation_windows_settings)

        # Run the navigation routine using given settings
        navigation_outputs = helper_functions.generate_navigation_outputs(
            observation_windows_settings,
            **auxilary_settings)

        process_multiple_navigation_results = ProcessNavigationResults.PlotMultipleNavigationResults(
            navigation_outputs,
            color_cycle=["salmon", "forestgreen"],
            figure_settings={"save_figure": self.save_figure,
                            "current_time": self.current_time,
                            "file_name": self.file_name
            }
        )

        evaluation_threshold = self.optimization_results["evaluation_threshold"]
        process_multiple_navigation_results.plot_full_state_history_comparison()
        process_multiple_navigation_results.plot_uncertainty_comparison()
        process_multiple_navigation_results.plot_maneuvre_costs(separate_plots=True)
        process_multiple_navigation_results.plot_maneuvre_costs(separate_plots=False)
        process_multiple_navigation_results.plot_monte_carlo_estimation_error_history(evaluation_threshold=evaluation_threshold)
        process_multiple_navigation_results.plot_maneuvre_costs_bar_chart(evaluation_threshold=evaluation_threshold, worst_case=False, bar_labeler=None)


    def plot_comparison_optimization_maneuvre_costs(self, process_optimization_results, compare_time_tags={}, show_observation_window_settings=False, custom_num_runs=None, custom_auxiliary_settings={}):

        optimization_keys = self.optimization_results["file_name"]
        time_tags = {optimization_keys: [self.optimization_results["current_time"]]}
        initial_design_vector = self.optimization_results["initial_design_vector"]

        if compare_time_tags:
            time_tags = compare_time_tags
        if custom_auxiliary_settings:
            auxilary_settings = custom_auxiliary_settings
        else:
            auxilary_settings = {}

        # Collect optimization results
        optimization_results_dict = {}
        for label, time_tags_list in time_tags.items():
            optimization_results_dict[label] = {}
            for time_tag in time_tags_list:
                file_name = self.file_name
                if label != self.optimization_results["file_name"]:
                    if "nelder_mead" in label or "Nelder-Mead" in label or "Nelder Mead" in label:
                        file_name = "optimization_analysis_nelder_mead"
                    elif "particle_swarm" in label or "Particle-Swarm" in label or "Particle Swarm" in label or "PSO" in label:
                        file_name = "optimization_analysis_particle_swarm"

                optimization_results_dict[label][time_tag] = self.optimization_model.load_from_json(time_tag, folder_name=file_name)


        num_runs = self.optimization_results["num_runs"]
        if custom_num_runs is not None:
            num_runs = custom_num_runs

        observation_windows_settings = {
            "Default": [
                (self.optimization_results["initial_observation_windows"], num_runs, None),
            ]
        }

        for key in optimization_results_dict.keys():
            observation_windows_settings.update({f"Optimized,\n {key}": [
                (optimization_results_dict[key][time_tag]["best_observation_windows"], num_runs, str(run))
                    for run, time_tag in enumerate(time_tags[key])
                ]
            }
        )

        if show_observation_window_settings:
            print("Observation window settings \n:", observation_windows_settings)

        # Run the navigation routine using given settings
        navigation_outputs = {}
        for index, key in enumerate(observation_windows_settings.keys()):

            if key != "Default":
                sub_key = list(optimization_results_dict.keys())[int(index-1)]
                for run, time_tag in enumerate(time_tags[sub_key]):
                    auxilary_settings = optimization_results_dict[sub_key][time_tag]["kwargs"]
                    auxilary_settings.pop("seed")

                    auxilary_settings.update(custom_auxiliary_settings)

            print("auxiliary_settings", auxilary_settings)

            sub_navigation_outputs = helper_functions.generate_navigation_outputs(
                {key: observation_windows_settings[key]},
                **auxilary_settings
            )

            navigation_outputs.update(sub_navigation_outputs)

        print(navigation_outputs)

        process_multiple_navigation_results = ProcessNavigationResults.PlotMultipleNavigationResults(
            navigation_outputs,
            color_cycle=["salmon", "forestgreen", "forestgreen", "forestgreen", "forestgreen", "forestgreen"],
            figure_settings={"save_figure": self.save_figure,
                            "current_time": self.current_time,
                            "file_name": self.file_name
            }
        )

        evaluation_threshold = self.optimization_results["evaluation_threshold"]
        # process_multiple_navigation_results.plot_full_state_history_comparison()
        # process_multiple_navigation_results.plot_uncertainty_comparison()
        # process_multiple_navigation_results.plot_maneuvre_costs(separate_plots=True)
        # process_multiple_navigation_results.plot_maneuvre_costs(separate_plots=False)
        # process_multiple_navigation_results.plot_monte_carlo_estimation_error_history(evaluation_threshold=evaluation_threshold)
        process_multiple_navigation_results.plot_maneuvre_costs_bar_chart(show_annual=False, evaluation_threshold=evaluation_threshold, worst_case=False, bar_labeler=None)
        process_multiple_navigation_results.plot_maneuvre_costs_bar_chart(show_annual=True, evaluation_threshold=evaluation_threshold, worst_case=False, bar_labeler=None)



    def tabulate_optimization_results(self, compare_time_tags=[]):

        if self.save_table:
            table_generator = TableGenerator.TableGenerator(
                table_settings={"save_table": self.save_table,
                                "current_time": self.current_time,
                                "file_name": self.file_name})
            current_time = self.optimization_results["current_time"]

            table_generator.generate_optimization_analysis_table(
                self.optimization_results,
                file_name=f"{current_time}.tex"
            )

            if len(compare_time_tags) != 0:

                optimization_results_list = []
                for time_tag in compare_time_tags:
                    optimization_results = self.optimization_model.load_from_json(time_tag, folder_name=self.file_name)
                    optimization_results_list.append(optimization_results)

                table_generator.generate_statistics_table(
                    optimization_results_list,
                    file_name=f"{current_time}_statistics_table"
                )

                table_generator.generate_design_vector_table(
                    optimization_results_list,
                    file_name=f"{current_time}_design_vector_table"
                )