"""Script for plotting the projected DOS.

This script initializes the project, processes the data, and plots the projected DOS
using the provided configuration and data processing modules.
"""
import argparse
import os
from sys import argv

from core.config import load_config
from core.project_setup import initialize_project
from data.data_processor import process_pdos_data
from data.data_collector import prepare_pdos_info
from ui.ui_helpers import print_warning
from plotting.plot_handler import plot_pdos


parser = argparse.ArgumentParser(description="Plot projected band structure.")
parser.add_argument(
    "--plot-config",
    type=str,
    help="Path to a custom YAML plot configuration file. "
         "This file can be a partial config to override defaults."
)
args = parser.parse_args(argv[2:])

# Initialization of the project
project = initialize_project(argv, is_input=False, is_pdos=True)

# Prepare the DFT information for the project
prepare_pdos_info(project)

# Process the band data for the project
process_pdos_data(project)

# Setting the plot configuration
plot_config_file = None
if args.plot_config:
    if os.path.exists(args.plot_config):
        plot_config_file = args.plot_config
    else:
        print_warning(f"Plot config file '{args.plot_config}' not found. Using default config.")

plot_config = load_config(plot_config_file, config_type="dos")

# Plotting the band structure (set save_fig to True if you want to save the figure)
plot_pdos(project, plot_config, save_fig=False)