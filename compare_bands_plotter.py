""" Script to plot the comparison of DFT and Wannier band sctructures.

This script initializes a project, processes Wannier and DFT comparison data, and generates comparison plots.
"""
from sys import argv

from core.config import load_config
from core.project_setup import initialize_project
from data.data_processor import process_comparison_data
from data.data_collector import prepare_wannier_info
from utils.plot_handler import plot_wannier_comparison

# Initializing the project
project = initialize_project(argv, is_input=False, is_wannier=True)

# Preparing Wannier-related information for the initialized project.
prepare_wannier_info(project)

# Processing the comparison data for Wannier and DFT band structures.
process_comparison_data(project)

# Setting the plot configuration
plot_config = load_config(config_type="bands")

# Plotting the comparison of DFT and Wannier band structures.
plot_wannier_comparison(project, save_fig=False)