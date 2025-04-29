"""Script for plotting the projected band structure.

This script initializes the configuration, processes the data, and plots the projected band structure
using the provided configuration and data processing modules.
"""

from plot_handler import *
from data_processor import *


# Initialization of the configuration
config = prepare_paths()
config = prepare_dft_info(config)
config = process_band_data(
    config,
    config["paths"]["projbands_paths"],
    config["paths"]["bands_paths"],
    config["number_of_bands_list"],
    config["fermi_energy_list"],
    config["project_dir"],
    config["atomic_states_info_list"],
    config["atomic_states_info_list"][0].keys()
)

# Plotting the band structure
plot_band_structure(config, save_fig=False)