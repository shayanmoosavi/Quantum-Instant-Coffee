"""Script to write input files for the project.

This script is designed to be run from the command line and takes two arguments:
1. `compound_name`: The name of the compound (e.g., 'GaAs', 'SiO2').
2. `poscar_file`: The path to the POSCAR file.
"""
import argparse
from sys import argv

from core.project_setup import initialize_project
from input.input_file_generator import InputFileManager

# Creating the parser
parser = argparse.ArgumentParser(description="Writes input files for Quantum ESPRESSO and Wannier90 calculations.")

# Adding arguments
parser.add_argument(
    "compound_name",
    type=str,
    help="Name of the compound (e.g., 'GaAs', 'SiO2')."
)
parser.add_argument(
    "poscar_file",
    type=str,
    help="Path to the POSCAR file."
)
parser.add_argument(
    "config_type",
    type=str,
    choices=["default", "bands", "pdos", "wannier"],
    default="default",
    help="Type of configuration to use (default, bands, pdos, wannier). Defaults to 'default'."
)
parser.add_argument(
    "--project-config",
    type=str,
    help="Path to a custom JSON project configuration file."
)

# Parsing the arguments
args = parser.parse_args(argv[1:])
compound_name, poscar_file = args.compound_name, args.poscar_file
config_type = args.config_type
config_file = args.project_config

project = initialize_project(compound_name,
                             config_file,
                             config_type,
                             poscar_file,
                             is_input=True)

skip_soc = project.skip_soc
manager = InputFileManager(project)
manager.write_all_input_files(skip_soc)