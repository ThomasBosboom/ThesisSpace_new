import os
import sys
import numpy as np
import itertools
from datetime import datetime
import matplotlib.pyplot as plt
import multiprocessing
from functools import partial

# Define path to import src files
file_name = os.path.splitext(os.path.basename(__file__))[0]
file_directory = os.path.realpath(__file__)
for _ in range(4):
    file_directory = os.path.dirname(file_directory)
    sys.path.append(file_directory)

# Define current time
current_time = datetime.now().strftime("%Y%m%d%H%M")

# Own
from src import NavigationSimulator, ObjectiveFunctions
from tests.postprocessing import ProcessOptimizationResults, OptimizationModel
from optimization_analysis_helper_functions import check_file_exists, process_case


def run_comparison_analysis(custom_tag):

    ##############################################################
    #### Optimization settings ###################################
    ##############################################################

    cases = {
        "delta_v_min": [0.00],
    }

    auto_mode = False
    # custom_tag = "default28dur1len3int"
    num_optims = 5

    duration = 28
    arc_length = 1
    arc_interval = 3

    bounds = (0.1, 2.0)
    max_iterations = 1
    test_objective = False

    use_same_seed = False
    run_optimization = False
    plot_full_comparison_cases = [[0, 1, 2, 3, 4], 5]
    from_file = True


    ##############################################################
    #### Processing logic ########################################
    ##############################################################

    if custom_tag is not None:
        current_time = custom_tag
    if auto_mode:
        if custom_tag is not None:
            current_time = custom_tag
        from_file = check_file_exists(cases, current_time, num_optims, file_name)
        run_optimization = True


    ##############################################################
    #### Default optimization settings ###########################
    ##############################################################

    navigation_simulator_settings = {
        "show_corrections_in_terminal": True,
        "run_optimization_version": True,
        "model_name": "PMSRP",
        "model_name_truth": "PMSRP"
    }

    objective_functions_settings = {
        "evaluation_threshold": 14,
        "num_runs": 1,
        "seed": 0
    }

    optimization_model_settings = {
        "duration": duration,
        "arc_length": arc_length,
        "arc_interval": arc_interval,
        "bounds": bounds,
        "max_iterations": max_iterations,
        "show_evaluations_in_terminal": True,
        "optimization_method": "Nelder-Mead",
        "design_vector_type": "arc_lengths",
        "initial_simplex_perturbation": -arc_length/2,
        "use_random_initial_design_vector": False
    }


    ##############################################################
    #### Start of main loop ######################################
    ##############################################################

    keys, values = zip(*cases.items())
    case_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

    # Use multiprocessing.Pool to parallelize the loop
    # num_workers = multiprocessing.cpu_count()
    num_workers = num_optims
    with multiprocessing.Pool(processes=num_workers) as pool:
        partial_process_case = partial(
            process_case,
            navigation_simulator_settings=navigation_simulator_settings,
            objective_functions_settings=objective_functions_settings,
            optimization_model_settings=optimization_model_settings,
            run_optimization=run_optimization,
            from_file=from_file,
            custom_tag=current_time,
            file_name=file_name,
            test_objective=test_objective,
            use_same_seed=use_same_seed,
            plot_full_comparison_cases=plot_full_comparison_cases)

        case_runs = [(case, run) for case in case_combinations for run in range(num_optims)]
        results = pool.starmap(partial_process_case, case_runs)

    # Select only first case run as example
    process_optimization_result = results[0]
    process_optimization_result.plot_iteration_history(
        show_design_variables=False,
        compare_time_tags={"Nelder-Mead": [result.time_tag for result in results]}
    )

    process_optimization_result.tabulate_optimization_results(
        compare_time_tags=[result.time_tag for result in results]
    )

    # plt.show()


if __name__ == "__main__":

    custom_tags = ["default28dur1len3int"]
    for custom_tag in custom_tags:
        run_comparison_analysis(custom_tag)

    plt.show()