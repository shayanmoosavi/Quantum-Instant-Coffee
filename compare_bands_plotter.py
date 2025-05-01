""" Script to plot the comparison of DFT and Wannier band sctructures.

This script initializes a project, processes Wannier and DFT comparison data, and generates comparison plots.
"""
from plot_handler import *
from data_processor import *

# Initializing the project
project = initialize_project(argv, is_input=False, is_wannier=True)

# Preparing Wannier-related information for the initialized project.
prepare_wannier_info(project)

# Processing the comparison data for Wannier and DFT band structures.
process_comparison_data(project)

# Plotting the comparison of DFT and Wannier band structures.
plot_wannier_comparison(project, save_fig=False)