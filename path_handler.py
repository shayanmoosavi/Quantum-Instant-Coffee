"""Module for managing file paths.

This module provides functions to handle file paths for Quantum ESPRESSO calculations.
It includes functionality for validating command-line arguments, creating directory structures,
and building structured file paths for input and output files.
"""

import os
from sys import argv
from config import load_config
from input_handler import get_pbands_type, get_strain_amounts


def validate_command_line_args(args, is_for_plot=False):
    """
    Validate command line arguments.

    Args:
    args (list): List of command line arguments.
    is_for_plot (bool): Whether the command line arguments are validated for plotting or input file generation.

    Returns:
        str or tuple: The compound name (and optionally the POSCAR file) provided as command line arguments.

    Raises:
        SystemExit: If the required arguments are missing or too many arguments are provided.
    """
    if is_for_plot:
        if len(args) < 2:
            print("Error: Missing compound name argument")
            print("Usage: python <script>.py <compound_name>")
            exit(1)
        return args[1]
    else:
        if len(args) < 3:
            print("Error: Missing compound name and/or POSCAR file argument")
            print("Usage: python <script>.py <compound_name> <poscar_file>")
            exit(1)
        if len(args) > 3:
            print("Error: Too many arguments provided")
            print("Usage: python <script>.py <compound_name> <poscar_file>")
            exit(1)
        return args[1], args[2]


def get_project_directory(compound_name):
    """
    Get the project directory for the given compound.

    Args:
        compound_name (str): Name of the compound.

    Returns:
        str: The absolute path to the project directory.
    """
    root_dir = os.path.abspath("../")  # The root directory of the project
    return os.path.join(root_dir, compound_name)  # The calculation directory


def append_file_paths(file_paths, calculation, path, compound_name, file_patterns, flag, keys):
    """
    Append file paths to the file_paths dictionary for a specific calculation.

    Args:
        file_paths (dict): Dictionary to store file paths.
        calculation (str): The calculation type (e.g., 'scf', 'strain').
        path (str): The base directory path for the calculation.
        compound_name (str): Name of the compound.
        file_patterns (dict): File naming patterns for the calculation.
        flag (str): Additional flag for the calculation (e.g., '_soc').
        keys (list): List of keys for which paths need to be appended.
    """
    for key in keys:
        if key not in file_paths[calculation]:
            file_paths[calculation][key] = []
        file_paths[calculation][key].append(os.path.join(
            path,
            file_patterns[key].format(compound_name=compound_name, flag=flag)
        ))


def add_paths_for_directories(
        calculation_dirs,
        compound_name,
        file_patterns,
        file_paths,
        is_input=True,
        include_stress=False,
        stress_amounts=None
):
    """
    Add file paths for the given directory structure.

    Args:
        calculation_dirs (dict): Mapping of calculation types to their directory paths.
        compound_name (str): Name of the compound.
        file_patterns (dict): File naming patterns for the calculations.
        file_paths (dict): Dictionary to store file paths.
        is_input (bool): Whether the paths are for input files.
        include_stress (bool): Whether to include strain analysis paths.
        stress_amounts (list, optional): List of strain amounts. Defaults to None.
    """
    for calculation, path in calculation_dirs.items():

        flag = "_soc" if "soc" in calculation else ""
        if include_stress and calculation == "strain":
            for stress_amount in stress_amounts:
                append_file_paths(file_paths, calculation,
                                  os.path.join(path, stress_amount), compound_name, file_patterns, flag,
                                  ["pw_bands_input", "kpdos_input", "bands_input"] if is_input else
                                  ["pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"])

        elif calculation == "strain":
            continue
        elif calculation in ["wannier", "wannier_soc"] and not is_input:
            continue

        elif calculation in ["scf", "scf_soc"]:

            append_file_paths(file_paths, calculation, path, compound_name, file_patterns,
                              flag, ["vc_relax_input", "scf_input"] if is_input else
                              ["scf_output"])

        elif calculation in ["projected_bands", "projected_bands_soc"]:

            append_file_paths(file_paths, calculation, path, compound_name, file_patterns,
                              flag, ["pw_bands_input", "kpdos_input", "bands_input"] if is_input else
                              ["pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"])

        else:
            if is_input:
                append_file_paths(file_paths, calculation, path, compound_name, file_patterns, flag,
                                  ["nscf_wannier_input", "pw2wan_input", "wannier_input"])


def build_file_paths(
        project_dir, compound_name, config, is_input=False, include_stress=False, stress_amounts=None
):
    """
    Build file paths based on the analysis type.

    Args:
        project_dir (str): Path to the project directory.
        compound_name (str): Name of the compound.
        config (dict): Configuration dictionary.
        is_input (bool): Whether to build paths for input files.
        include_stress (bool): Whether to include stress analysis.
        stress_amounts (list, optional): List of strain amounts. Defaults to None.

    Returns:
        dict: Structured file paths for the calculations.
    """
    if is_input:
        dir_structure = config["directory_structure"]
        file_patterns = config["file_patterns"]["input"]
        calculation_dirs = {calculation: os.path.join(project_dir, path) for calculation, path in dir_structure.items()}
        input_file_paths = {calculation: {} for calculation in dir_structure.keys()}
        add_paths_for_directories(calculation_dirs, compound_name, file_patterns, input_file_paths, is_input,
                                  include_stress, stress_amounts)

        paths = {key: value for key, value in input_file_paths.items() if value}
        structured_paths = {
            "vc_relax_input_paths": [],
            "scf_input_paths": [],
            "pw_bands_input_paths": [],
            "kpdos_input_paths": [],
            "bands_input_paths": [],
            **(
                {
                    "nscf_wannier_input_paths": [],
                    "pw2wan_input_paths": [],
                    "wannier_input_paths": []
                } if not include_stress else {}
            )
        }

        for key, value in paths.items():
            if key in ["scf", "scf_soc"] and not (include_stress and "soc" in key):
                for path_type in ["vc_relax_input", "scf_input"]:
                    structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif key == "strain" and include_stress:

                for i in range(len(stress_amounts)):
                    for path_type in ["pw_bands_input", "kpdos_input", "bands_input"]:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][i])

            elif (not (include_stress and "soc" in key)) and key not in ["wannier", "wannier_soc"]:
                for path_type in ["pw_bands_input", "kpdos_input", "bands_input"]:
                    structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif key in ["wannier", "wannier_soc"] and not include_stress:
                for path_type in ["nscf_wannier_input", "pw2wan_input", "wannier_input"]:
                    structured_paths[f"{path_type}_paths"].append(value[path_type][0])

        return structured_paths

    else:
        dir_structure = config["directory_structure"]
        file_patterns = config["file_patterns"]["output"]
        calculation_dirs = {calculation: os.path.join(project_dir, path) for calculation, path in dir_structure.items()}
        output_file_paths = {calculation: {} for calculation in dir_structure.keys()}
        add_paths_for_directories(calculation_dirs, compound_name, file_patterns, output_file_paths, is_input,
                                  include_stress, stress_amounts)

        paths = {key: value for key, value in output_file_paths.items() if value}
        structured_paths = {
            "scf_output_paths": [],
            "pw_bands_output_paths": [],
            "kpdos_output_paths": [],
            "projbands_paths": [],
            "bands_paths": [],
        }

        for key, value in paths.items():
            if key in ["scf", "scf_soc"] and not (include_stress and "soc" in key):
                structured_paths["scf_output_paths"].append(value["scf_output"][0])

            elif key == "strain" and include_stress:

                for i in range(len(stress_amounts)):
                    for path_type, output_key in zip(
                            ["pw_bands_output_paths", "kpdos_output_paths", "projbands_paths", "bands_paths"],
                            ["pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"]
                    ):
                        structured_paths[path_type].append(value[output_key][i])

            elif not (include_stress and "soc" in key):
                for path_type, output_key in zip(
                        ["pw_bands_output_paths", "kpdos_output_paths", "projbands_paths", "bands_paths"],
                        ["pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"]
                ):
                    structured_paths[path_type].append(value[output_key][0])

        return structured_paths, include_stress


def create_directories(project_dir, dir_structure, include_stress=False, stress_amounts=None):
    """
    Creates the directory structure for the project.

    Args:
        project_dir (str): The path to the main project directory.
        dir_structure (dict): The directory structure of the project, mapping calculation types to directory paths.
        include_stress (bool): Whether to include strain analysis directories. Defaults to False.
        stress_amounts (list, optional): List of strain amounts to create subdirectories for, if strain analysis is included.

    Returns:
        list: A list of absolute paths to the created directories.

    Raises:
        OSError: If there is an error creating the directories.
    """
    try:
        # Creating main project directory if it doesn't exist
        os.makedirs(project_dir, exist_ok=True)
        print(f"\nProject directory initialized at:\n {project_dir}\n", flush=True)

        # Changing current directory to project directory
        os.chdir(project_dir)

        # List to store the paths of created directories
        calculation_dirs = []

        # Creating directories for each calculation type
        for calculation, path in dir_structure.items():

            if not include_stress and calculation == "strain":
                continue  # Skip creation of strain directories if not needed
            if calculation in ["pseudo", "pseudo_rel"]:
                # Skipping the creation of Pseudopotential directories as it needs to exist before running this script
                continue

            if include_stress:
                if calculation == "strain":
                    # Creating subdirectories for each strain amount if strain analysis is included
                    for stress_amount in stress_amounts:
                        stress_path = os.path.join(path, stress_amount)
                        os.makedirs(stress_path, exist_ok=True)
                        calculation_dirs.append(os.path.abspath(stress_path))
                else:
                    # Creating other calculation directories
                    os.makedirs(path, exist_ok=True)
                    calculation_dirs.append(os.path.abspath(path))
            else:
                # Creating directories for calculations other than strain
                os.makedirs(path, exist_ok=True)
                calculation_dirs.append(os.path.abspath(path))

        print("Successfully created calculation directories.\n", flush=True)

        # Changing the directory to the root directory of the script
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        return calculation_dirs  # Return the list of created directories

    except OSError as e:
        print(f"Error creating directories: {e}")
        return []  # Return an empty list to indicate failure


def prepare_paths(is_input=False):
    """
    Prepare paths for the Quantum ESPRESSO calculations.

    Args:
    is_input (bool): Whether to prepare paths for input files. Defaults to False.

    Returns:
        dict: A dictionary containing the prepared paths and related metadata.
    """
    print("Initializing...\n")

    if not is_input:

        # Load configuration for output file paths
        config = load_config()

        # Validate command-line arguments for plotting
        compound_name = validate_command_line_args(argv, is_for_plot=True)

        # Get the project directory for the compound
        project_dir = get_project_directory(compound_name)

        # Determine if strain analysis is included
        include_stress = get_pbands_type()

        # Get the list of strain amounts if strain analysis is included
        stress_amounts = get_strain_amounts() if include_stress else None

        # Build file paths for output files
        paths, skip_soc = build_file_paths(
            project_dir, compound_name, config, is_input, include_stress, stress_amounts
        )

        # Return the prepared paths and metadata
        return {
            "compound_name": compound_name,
            "project_dir": project_dir,
            "include_stress": include_stress,
            "paths": paths,
            "skip_soc": skip_soc,
            "stress_amounts": stress_amounts,
        }

    else:

        # Load configuration for input file paths
        config = load_config()

        # Validate command-line arguments for input file generation
        compound_name, poscar_file = validate_command_line_args(argv)

        # Get the project directory for the compound
        project_dir = get_project_directory(compound_name)

        # Get the list of strain amounts for input files
        stress_amounts = get_strain_amounts(is_input)
        include_stress = True if stress_amounts else False

        # Build file paths for input files
        paths = build_file_paths(
            project_dir, compound_name, config, is_input, include_stress, stress_amounts
        )

        # Return the prepared paths and metadata
        return {
            "compound_name": compound_name,
            "project_dir": project_dir,
            "include_stress": include_stress,
            "paths": paths,
            "stress_amounts": stress_amounts,
        }


# Test to ensure the module works as expected
if __name__ == "__main__":
    """
    Main entry point for testing the module.
    
    Validates the functionality of the `prepare_paths` function and checks if all required files exist.
    """

    if len(argv) == 3:

        # Preparing paths for input files
        calculation = prepare_paths(is_input=True)
        print("Test information for debugging: \n")
        for key, value in calculation.items():

            if key == "paths":
                for path_type, paths in value.items():
                    print(f"{path_type}: {paths}")
            else:
                print(f"{key}: {value}")
    else:

        # Preparing paths for output files
        calculation = prepare_paths()

        # Checking if all required files exist
        failure = False
        for paths in list(calculation["paths"].values())[:-1]:
            for path in paths:
                if not os.path.exists(path):
                    print(f"path '{path}' does not exist!")
                    failure = True
                else:
                    print(f"path '{path}' exists.")

        if failure:
            print("Test failed!")
            exit(1)
        else:
            print("Test passed!")

        print("Test information for debugging: \n")

        print(f"Compound Name: {calculation['compound_name']}")
        print(f"Project Directory: {calculation['project_dir']}")
        print(f"Include Stress: {calculation['include_stress']}")
        print(f"Stress Amounts: {calculation['stress_amounts']}")
        print("\nDirectory Structure:")
        for key, value in calculation["paths"].items():
            print(f"{key}: {value}")
