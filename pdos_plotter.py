"""Script for plotting the projected DOS.

This script initializes the project, processes the data, and plots the projected DOS
using the provided configuration and data processing modules.
"""

from sys import argv

from core.project_setup import initialize_project
from data.data_processor import process_pdos_data
from data.dft_info_extractor import prepare_pdos_info
from utils.plot_handler import DOSPlotConfig, plot_pdos

# Initialization of the project
project = initialize_project(argv, is_input=False, is_pdos=True)

# Prepare the DFT information for the project
prepare_pdos_info(project)

# Process the band data for the project
process_pdos_data(project)

# Setting the plot configuration
plot_config = DOSPlotConfig()
# You can modify the plot configuration here
# ...

# Plotting the band structure (set save_fig to True if you want to save the figure)
plot_pdos(project, plot_config, save_fig=False)