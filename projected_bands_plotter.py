"""Script for plotting the projected band structure.

This script initializes the project, processes the data, and plots the projected band structure
using the provided configuration and data processing modules.
"""
from sys import argv

from core.project_setup import initialize_project
from data.data_processor import process_band_data
from data.data_collector import prepare_bands_info
from utils.plot_handler import BandsPlotConfig, plot_band_structure


# Initialization of the project
project = initialize_project(argv, is_input=False)

# Prepare the DFT information for the project
prepare_bands_info(project)

# Process the band data for the project
process_band_data(project)

# Setting the plot configuration
plot_config = BandsPlotConfig()
# You can modify the plot configuration here
# ...

# Plotting the band structure (set save_fig to True if you want to save the figure)
plot_band_structure(project, plot_config, save_fig=False)