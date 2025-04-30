"""Script for plotting the projected band structure.

This script initializes the configuration, processes the data, and plots the projected band structure
using the provided configuration and data processing modules.
"""

from plot_handler import *
from data_processor import *


# Initialization of the configuration
project = initialize_project(argv, is_input=False)
prepare_dft_info(project)
process_band_data(project)

# Plotting the band structure
plot_band_structure(project, save_fig=False)