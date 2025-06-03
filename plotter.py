"""
Main script for plotting band structures, Wannier comparisons, and PDOS.

This script initializes the project, prepares the necessary data, processes it,
and generates the plots based on the specified plot type.
"""
import argparse
import os
from sys import argv

from core.config import load_plot_config
from core.path import initialize_project
from data.collectors import *
from data.processors import *
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
    "--project-config",
    type=str,
    help="Path to a custom JSON project configuration file."
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

parser.add_argument(
    "--skip-soc",
    action="store_true",
    help="Skip generation of plots with spin-orbit coupling (SOC)."
)

parser.add_argument(
    "--skip-normal",
    action="store_true",
    help="Skip generation of plots without spin-orbit coupling (SOC)."
)

# Parsing the arguments
args = parser.parse_args(argv[1:])
compound_name = args.compound_name
project_config_file = args.project_config

# Initialize project based on plot type
if args.plot_type == "bands":
    project = initialize_project(compound_name,
                                 project_config_file,
                                 config_type="bands",
                                 is_input=False,
                                 skip_soc=args.skip_soc,
                                 skip_normal=args.skip_normal)
    prepare_bands_info(project)
    process_band_data(project)

elif args.plot_type == "wannier":
    project = initialize_project(compound_name,
                                 project_config_file,
                                 config_type="wannier",
                                 is_input=False,
                                 is_wannier=True,
                                 skip_soc=args.skip_soc,
                                 skip_normal=args.skip_normal)
    prepare_wannier_info(project)
    process_comparison_data(project)

elif args.plot_type == "pdos":
    project = initialize_project(compound_name,
                                 project_config_file,
                                 config_type="pdos",
                                 is_input=False,
                                 is_pdos=True,
                                 skip_soc=args.skip_soc,
                                 skip_normal=args.skip_normal)
    prepare_pdos_info(project)
    process_pdos_data(project)

else:
    raise ValueError("Invalid plot type.")

# Load plot configuration
plot_config_file = None
if args.plot_config:
    if os.path.exists(args.plot_config):
        plot_config_file = args.plot_config
    else:
        print_warning(f"Plot config file '{args.plot_config}' not found. Using default config.")

plot_config = load_plot_config(plot_config_file, config_type="pdos" if args.plot_type == "pdos" else "bands")

# Plotting
if args.plot_type == "bands":
    plot_band_structure(project, plot_config, save_fig=args.save_fig)
elif args.plot_type == "wannier":
    plot_wannier_comparison(project, plot_config, save_fig=args.save_fig)
elif args.plot_type == "pdos":
    plot_pdos(project, plot_config, save_fig=args.save_fig)
