"""Module for managing file paths.

This module provides functions to handle file paths for Quantum ESPRESSO calculations.
It includes functionality for validating command-line arguments, creating directory structures,
and building structured file paths for input and output files.
"""

from sys import argv

from config import ProjectConfig
from project_setup import *
from typing import List, Tuple, Dict

def validate_command_line_args(args: List[str], is_for_plot: bool = False) -> str | Tuple[str, str]:
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


def get_project_directory(compound_name: str) -> str:
    """
    Get the project directory for the given compound.

    Args:
        compound_name (str): Name of the compound.

    Returns:
        str: The absolute path to the project directory.
    """
    root_dir = os.path.abspath("../")  # The root directory of the project
    return os.path.join(root_dir, compound_name)  # The calculation directory


def append_file_paths(file_paths: Dict[str, Dict[str, List[str]]],
                      calculation: str,
                      path: str,
                      compound_name: str,
                      file_patterns: Dict[str, str],
                      flag: str,
                      keys: List[str]) -> None:
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
        try:
            if key not in file_paths[calculation]:
                file_paths[calculation][key] = []
            file_paths[calculation][key].append(os.path.join(
                path,
                file_patterns[key].format(compound_name=compound_name, flag=flag)
            ))
        except KeyError:
            print(f"Key '{key}' not found in provided config. Skipping...")
            continue


def add_paths_for_directories(
        calculation_dirs: Dict[str, str],
        compound_name: str,
        file_patterns: Dict[str, str],
        file_paths: Dict[str, Dict[str, List[str]]],
        is_input: bool = True,
        include_stress: bool = False,
        stress_amounts: List[str] = None
) -> None:
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
        elif calculation in ["pseudo", "pseudo_rel"]:
            continue
        elif calculation in ["scf", "scf_soc"]:

            append_file_paths(file_paths, calculation, path, compound_name, file_patterns,
                              flag, ["relax_input", "vc_relax_input", "scf_input"] if is_input else
                              ["scf_output"])

        elif calculation in ["projected_bands", "projected_bands_soc"]:

            append_file_paths(file_paths, calculation, path, compound_name, file_patterns,
                              flag, ["pw_bands_input", "kpdos_input", "bands_input"] if is_input else
                              ["pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"])

        elif calculation in ["pdos", "pdos_soc"]:
            append_file_paths(file_paths, calculation, path, compound_name, file_patterns,
                              flag, ["nscf_input", "pdos_input"] if is_input else ["nscf_output"])

        elif calculation in ["wannier", "wannier_soc"]:
                append_file_paths(file_paths, calculation, path, compound_name, file_patterns, flag,
                                  ["nscf_wannier_input", "pw2wan_input", "wannier_input"] if is_input
                                  else ["nscf_wannier_output", "wannier_bands"])


def build_file_paths(
        project_dir: str,
        compound_name: str,
        config: ProjectConfig,
        is_input: bool = False,
        include_stress: bool = False,
        stress_amounts: bool = None
) -> Dict[str, List[str]] | Tuple[Dict[str, List[str]], bool]:
    """
    Build file paths based on the analysis type.

    Args:
        project_dir (str): Path to the project directory.
        compound_name (str): Name of the compound.
        config (ProjectConfig): Project configuration object containing directory structure and file patterns.
        is_input (bool): Whether to build paths for input files.
        include_stress (bool): Whether to include stress analysis.
        stress_amounts (list, optional): List of strain amounts. Defaults to None.

    Returns:
        dict: Structured file paths for the calculations.
    """
    if is_input:
        dir_structure = config.directory_structure
        file_patterns = config.file_patterns.input
        calculation_dirs = {calculation: os.path.join(project_dir, path) for calculation, path in dir_structure.items()}
        input_file_paths = {calculation: {} for calculation in dir_structure.keys()}
        add_paths_for_directories(calculation_dirs, compound_name, file_patterns, input_file_paths, is_input,
                                  include_stress, stress_amounts)

        paths = {key: value for key, value in input_file_paths.items() if value}
        structured_paths = {
            "relax_input_paths": [],
            "vc_relax_input_paths": [],
            "scf_input_paths": [],
            "pw_bands_input_paths": [],
            "kpdos_input_paths": [],
            "bands_input_paths": [],
            "nscf_input_paths": [],
            "pdos_input_paths": [],
            **(
                {
                    "nscf_wannier_input_paths": [],
                    "pw2wan_input_paths": [],
                    "wannier_input_paths": []
                } if not include_stress else {}
            )
        }

        for key, value in paths.items():

            if key in ["pseudo", "pseudo_rel"]:
                continue # Skip pseudopotential directories

            if key in ["scf", "scf_soc"] and not (include_stress and "soc" in key):
                for path_type in [ "relax_input", "vc_relax_input", "scf_input"]:
                    if not value[path_type]:
                        print(f"Warning: No {path_type} found in {key} directory.")
                    else:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif key == "strain" and include_stress:

                for i in range(len(stress_amounts)):
                    for path_type in ["pw_bands_input", "kpdos_input", "bands_input"]:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][i])

            elif key in ["pdos", "pdos_soc"] and not (include_stress and "soc" in key):
                for path_type in ["nscf_input", "pdos_input"]:
                    if not value[path_type]:
                        print(f"Warning: No {path_type} found in {key} directory.")
                    else:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif (not (include_stress and "soc" in key)) and key not in ["wannier", "wannier_soc"]:
                for path_type in ["pw_bands_input", "kpdos_input", "bands_input"]:
                    structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif key in ["wannier", "wannier_soc"] and not include_stress:
                for path_type in ["nscf_wannier_input", "pw2wan_input", "wannier_input"]:
                    if not value[path_type]:
                        print(f"Warning: No {path_type} found in {key} directory.")
                    else:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][0])

        return {key: value for key, value in structured_paths.items() if value}

    else:
        dir_structure = config.directory_structure
        file_patterns = config.file_patterns.output
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
            "nscf_output_paths": [],
            "nscf_wannier_output_paths": [],
            "wannier_bands_paths": [],
        }

        for key, value in paths.items():

            if key in ["pseudo", "pseudo_rel"]:
                continue # Skip pseudopotential directories

            if key in ["scf", "scf_soc"] and not (include_stress and "soc" in key):
                structured_paths["scf_output_paths"].append(value["scf_output"][0])

            elif key == "strain" and include_stress:

                for i in range(len(stress_amounts)):
                    for path_type, output_key in zip(
                            ["pw_bands_output_paths", "kpdos_output_paths", "projbands_paths", "bands_paths"],
                            ["pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"]
                    ):
                        structured_paths[path_type].append(value[output_key][i])

            elif not (include_stress and "soc" in key) and key not in ["pdos", "pdos_soc", "wannier", "wannier_soc"]:
                for path_type, output_key in zip(
                        ["pw_bands_output_paths", "kpdos_output_paths", "projbands_paths", "bands_paths"],
                        ["pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"]
                ):
                    structured_paths[path_type].append(value[output_key][0])

            elif key in ["pdos", "pdos_soc"] and not (include_stress and "soc" in key):
                for path_type in ["nscf_output"]:
                    if not value[path_type]:
                        print(f"Warning: No {path_type} found in {key} directory.")
                    else:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif key in ["wannier", "wannier_soc"] and not include_stress:
                for path_type in ["nscf_wannier_output", "wannier_bands"]:
                    if not value[path_type]:
                        print(f"Warning: No {path_type} found in {key} directory.")
                    else:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][0])

        return {key: value for key, value in structured_paths.items() if value}, include_stress


def create_directories(project_dir: str,
                       dir_structure: Dict[str, str],
                       include_stress: bool = False,
                       stress_amounts: List[str] = None) -> List[str]:
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


# Test to ensure the module works as expected
if __name__ == "__main__":
    """
    Main entry point for testing the module.
    
    Validates the functionality of the `prepare_paths` function and checks if all required files exist.
    """
    is_input = len(argv) == 3

    try:
        # Initialize and prepare project
        project = initialize_project(argv, is_input)

        # Print summary
        print("\nInitialization complete. Project information:")
        print(f"  Compound name: {project.compound_name}")
        print(f"  Project directory: {project.project_dir}")
        print(f"  Include stress: {project.include_stress}")
        if project.include_stress:
            print(f"  Stress amounts: {project.stress_amounts}")
        print(f"  Pseudopotential directory: {project.pseudo_dir}")
        print(f"  Relativistic Pseudopotential directory: {project.rel_pseudo_dir}")
        if is_input:
            print(f"  Calculation directories: {project.calculation_dirs}")
        print(f"  Elements: {project.compound_data.element_names}")
        print(f"  Atomic labels: {project.compound_data.atomic_labels}")

        if is_input:
            print("\nInput paths:")
            for path_type, paths in project.input_paths.items():
                print(f"  {path_type}: {paths}")
        else:
            print("\nOutput paths:")
            for path_type, paths in project.output_paths.items():
                print(f"  {path_type}: {paths}")

    except ProjectInitializationError as e:
        print(f"Error during project initialization: {str(e)}")
        exit(1)

    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        exit(1)
