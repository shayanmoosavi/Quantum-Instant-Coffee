"""Minimal test to make sure path generation steps are correct"""

import os
from sys import argv
from config import load_config
import input_handler
import path_handler


def initialize_calculation():
    print("Initializing...\n")

    config = load_config()

    compound_name = path_handler.validate_command_line_args(argv)

    project_dir = path_handler.get_project_directory(compound_name)

    include_stress = input_handler.get_pbands_type()

    stress_amounts = input_handler.get_strain_amounts() if include_stress else None

    paths = path_handler.build_file_paths(
        project_dir, compound_name, include_stress, config, stress_amounts
    )

    fermi_energy = 0.0
    number_of_bands = 0

    return {
        "compound_name": compound_name,
        "fermi_energy": fermi_energy,
        "number_of_bands": number_of_bands,
        "project_dir": project_dir,
        "include_stress": include_stress,
        "paths": paths,
        "stress_amounts": stress_amounts,
    }


calculation = initialize_calculation()

# Checking if all required files exist
failure = False
for dir_list in list(calculation["paths"].values())[:-1]:
    for dir in dir_list:
        if not os.path.exists(dir):
            print(f"path '{dir}' does not exist!")
            failure = True
        else:
            print(f"path '{dir}' exists.")

if failure:
    print("Test failed!")
    exit(1)
else:
    print("Test passed!")

print("Test information for debugging: \n")

print(f"compound_name: {calculation['compound_name']}")
print(f"fermi_energy: {calculation['fermi_energy']}")
print(f"number_of_bands: {calculation['number_of_bands']}")
print(f"project_dir: {calculation['project_dir']}")
print(f"include_stress: {calculation['include_stress']}")
print(f"stress_amounts: {calculation['stress_amounts']}")
