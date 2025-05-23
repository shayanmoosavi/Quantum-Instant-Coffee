"""
Main script for plotting band structures, Wannier comparisons, and PDOS.

This script initializes the project, prepares the necessary data, processes it,
and generates the plots based on the specified plot type.
"""
import argparse
import os
from sys import argv

from core.config import load_config
from core.project_setup import initialize_project
from data.data_collector import prepare_bands_info, prepare_wannier_info, prepare_pdos_info
from data.data_processor import process_band_data, process_comparison_data, process_pdos_data
from plotting.plot_handler import plot_band_structure, plot_wannier_comparison, plot_pdos
from ui.ui_helpers import print_warning

# Creating the parser
parser = argparse.ArgumentParser(description="Plot band structures, Wannier comparisons, and PDOS.")

# Adding arguments
parser.add_argument(
    "compound_name",
    type=str,
    help="Name of the compound (e.g., 'GaAs', 'SiO2')."
)
parser.add_argument(
    "plot_type",
    type=str,
    choices=["bands", "wannier", "pdos"],
    help="Type of plot to generate (bands, wannier, pdos)."
)
parser.add_argument(
    "--plot-config",
    type=str,
    help="Path to a custom YAML plot configuration file. This file can be a partial config to override defaults."
)
parser.add_argument(
    "--save-fig",
    action="store_true",
    help="Save the figure to a file instead of displaying it."
)

# Parsing the arguments
args = parser.parse_args(argv[1:])
compound_name = args.compound_name


# Initialize project based on plot type
if args.plot_type == "bands":
    project = initialize_project(compound_name, is_input=False)
    prepare_bands_info(project)
    process_band_data(project)
    config_type = "bands"

elif args.plot_type == "wannier":
    project = initialize_project(compound_name, is_input=False, is_wannier=True)
    prepare_wannier_info(project)
    process_comparison_data(project)
    config_type = "bands"

elif args.plot_type == "pdos":
    project = initialize_project(compound_name, is_input=False, is_pdos=True)
    prepare_pdos_info(project)
    process_pdos_data(project)
    config_type = "dos"

else:
    raise ValueError("Invalid plot type.")

# Load plot configuration
plot_config_file = None
if args.plot_config:
    if os.path.exists(args.plot_config):
        plot_config_file = args.plot_config
    else:
        print_warning(f"Plot config file '{args.plot_config}' not found. Using default config.")

plot_config = load_config(plot_config_file, config_type=config_type)

# Plotting
if args.plot_type == "bands":
    plot_band_structure(project, plot_config, save_fig=args.save_fig)
elif args.plot_type == "wannier":
    plot_wannier_comparison(project, plot_config, save_fig=args.save_fig)
elif args.plot_type == "pdos":
    plot_pdos(project, plot_config, save_fig=args.save_fig)
