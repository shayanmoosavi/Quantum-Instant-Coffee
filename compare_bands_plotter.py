""" Script to plot the comparison of DFT and Wannier band sctructures.

This script initializes a project, processes Wannier and DFT comparison data, and generates comparison plots.
"""
import os
from sys import argv
import argparse

from core.config import load_config
from core.project_setup import initialize_project
from data.data_processor import process_comparison_data
from data.data_collector import prepare_wannier_info
from ui.ui_helpers import print_warning
from plotting.plot_handler import plot_wannier_comparison


parser = argparse.ArgumentParser(description="Plot projected band structure.")
parser.add_argument(
    "--plot-config",
    type=str,
    help="Path to a custom YAML plot configuration file. "
         "This file can be a partial config to override defaults."
)
args = parser.parse_args(argv[2:])

# Initializing the project
project = initialize_project(argv, is_input=False, is_wannier=True)

# Preparing Wannier-related information for the initialized project.
prepare_wannier_info(project)

# Processing the comparison data for Wannier and DFT band structures.
process_comparison_data(project)

# Setting the plot configuration
plot_config_file = None
if args.plot_config:
    if os.path.exists(args.plot_config):
        plot_config_file = args.plot_config
    else:
        print_warning(f"Plot config file '{args.plot_config}' not found. Using default config.")

plot_config = load_config(plot_config_file, config_type="bands")

# Plotting the comparison of DFT and Wannier band structures.
plot_wannier_comparison(project, plot_config, save_fig=False)