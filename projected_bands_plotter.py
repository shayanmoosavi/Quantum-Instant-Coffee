"""Script for plotting the projected band structure.

This script initializes the project, processes the data, and plots the projected band structure
using the provided configuration and data processing modules.
"""
from utils.plot_handler import *
from data.data_processor import *


# Initialization of the project
project = initialize_project(argv, is_input=False)

# Prepare the DFT information for the project
prepare_dft_info(project)

# Process the band data for the project
process_band_data(project)

# Plotting the band structure
plot_band_structure(project, save_fig=False)