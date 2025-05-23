"""Module for managing file paths.

This module provides functions to handle file paths for Quantum ESPRESSO calculations.
It includes functionality for validating command-line arguments, creating directory structures,
and building structured file paths for input and output files.
"""
import argparse
from sys import argv
import os
from typing import List, Tuple, Dict

from core.project_setup import initialize_project, ProjectInitializationError
from core.config_handler import ProjectConfig
from ui.ui_helpers import *


def get_project_directory(compound_name: str) -> str:
    """
    Get the project directory for the given compound.

    Args:
        compound_name (str): Name of the compound.

    Returns:
        str: The absolute path to the project directory.
    """
    script_root_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".."))  # The root directory of the program
    user_id = os.getenv("COFFEE")
    user_path = os.path.join(script_root_dir, "..", user_id) if user_id else ".."
    root_dir = os.path.abspath(user_path)  # The root directory of the project
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
            print_warning(f"Key '{key}' not found in provided config. Skipping...")
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
                                  ["scf_input", "pw_bands_input", "kpdos_input", "bands_input"] if is_input else
                                  ["scf_output", "pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"])

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
                              flag, ["nscf_input", "pdos_input"] if is_input else ["nscf_output", "pdos_output"])

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
        stress_amounts: List[str] = None
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
                continue  # Skip pseudopotential directories

            if key in ["scf", "scf_soc"] and not (include_stress and "soc" in key):
                for path_type in ["relax_input", "vc_relax_input", "scf_input"]:
                    if not value[path_type]:
                        print_warning(f"No {path_type} found in {key} directory.")
                    else:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif key == "strain" and include_stress:

                for i in range(len(stress_amounts)):
                    for path_type in ["scf_input", "pw_bands_input", "kpdos_input", "bands_input"]:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][i])

            elif key in ["pdos", "pdos_soc"] and not (include_stress and "soc" in key):
                for path_type in ["nscf_input", "pdos_input"]:
                    if not value[path_type]:
                        print_warning(f"No {path_type} found in {key} directory.")
                    else:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif (not (include_stress and "soc" in key)) and key not in ["wannier", "wannier_soc"]:
                for path_type in ["pw_bands_input", "kpdos_input", "bands_input"]:
                    structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif key in ["wannier", "wannier_soc"] and not include_stress:
                for path_type in ["nscf_wannier_input", "pw2wan_input", "wannier_input"]:
                    if not value[path_type]:
                        print_warning(f"No {path_type} found in {key} directory.")
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
            "pdos_output_paths": [],
            "nscf_wannier_output_paths": [],
            "wannier_bands_paths": [],
        }

        for key, value in paths.items():

            if key in ["pseudo", "pseudo_rel"]:
                continue  # Skip pseudopotential directories

            if key in ["scf", "scf_soc"] and not (include_stress and "soc" in key):
                structured_paths["scf_output_paths"].append(value["scf_output"][0])

            elif key == "strain" and include_stress:

                for i in range(len(stress_amounts)):
                    for path_type, output_key in zip(
                            ["scf_output_paths", "pw_bands_output_paths", "kpdos_output_paths", "projbands_paths",
                             "bands_paths"],
                            ["scf_output", "pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"]
                    ):
                        structured_paths[path_type].append(value[output_key][i])

            elif not (include_stress and "soc" in key) and key not in ["pdos", "pdos_soc", "wannier", "wannier_soc"]:
                for path_type, output_key in zip(
                        ["pw_bands_output_paths", "kpdos_output_paths", "projbands_paths", "bands_paths"],
                        ["pw_bands_output", "kpdos_output", "projbands_output", "bands_gnu"]
                ):
                    structured_paths[path_type].append(value[output_key][0])

            elif key in ["pdos", "pdos_soc"] and not (include_stress and "soc" in key):
                for path_type in ["nscf_output", "pdos_output"]:
                    if not value[path_type]:
                        print_warning(f"No {path_type} found in {key} directory.")
                    else:
                        structured_paths[f"{path_type}_paths"].append(value[path_type][0])

            elif key in ["wannier", "wannier_soc"] and not include_stress:
                for path_type in ["nscf_wannier_output", "wannier_bands"]:
                    if not value[path_type]:
                        print_warning(f"No {path_type} found in {key} directory.")
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
        print_success(f"\nProject directory initialized at:\n {project_dir}\n")

        # Changing current directory to project directory
        os.chdir(project_dir)

        # List to store the paths of created directories
        calculation_dirs = []

        # Creating a table to show directory creation progress
        table = Table(title="Directory Creation Progress")
        table.add_column("Calculation Type", style="cyan")
        table.add_column("Status")

        print_header("Directory Creation")
        print('\n')

        # Creating directories for each calculation type
        for calculation, path in dir_structure.items():

            if not include_stress and calculation == "strain":
                continue  # Skip creation of strain directories if not needed
            if calculation in ["pseudo", "pseudo_rel"]:
                # Skipping the creation of Pseudopotential directories as it needs to exist before running this script
                continue
            try:
                if include_stress:
                    if calculation == "strain":
                        # Creating subdirectories for each strain amount if strain analysis is included
                        for stress_amount in stress_amounts:
                            stress_path = os.path.join(path, stress_amount)
                            os.makedirs(stress_path, exist_ok=True)
                            calculation_dirs.append(os.path.abspath(stress_path))
                            table.add_row(f"strain_{stress_amount}", "[green]✓ Created[/green]")
                    else:
                        # Creating other calculation directories
                        os.makedirs(path, exist_ok=True)
                        calculation_dirs.append(os.path.abspath(path))
                else:
                    # Creating directories for calculations other than strain
                    os.makedirs(path, exist_ok=True)
                    calculation_dirs.append(os.path.abspath(path))
                    table.add_row(calculation, "[green]✓ Created[/green]")

            except OSError as e:
                table.add_row(calculation, "[bold red]✗ Failed[/bold red]")
                print_error(f"Error creating directory: \n{str(e)}")

        console.print(table)
        print_success("\nSuccessfully created calculation directories.\n")

        # Changing the directory to the root directory of the script
        script_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        os.chdir(script_root_dir)

        return calculation_dirs  # Return the list of created directories

    except OSError as e:
        print_error(f"Error creating directories: {e}")
        return []  # Return an empty list to indicate failure


# Test to ensure the module works as expected
if __name__ == "__main__":
    """
    Main entry point for testing the module.
    
    Validates the functionality of the `prepare_paths` function and checks if all required files exist.
    """
    def validate_compound_name(value):
        if os.path.sep in value or os.path.altsep and os.path.altsep in value:
            raise argparse.ArgumentTypeError(f"'{value}' is not a valid compound name as it contains path separators.")
        return value

    # Create the parser
    parser = argparse.ArgumentParser(description="Tests the path handler module.")

    # Add arguments
    parser.add_argument(
        "compound_name",
        type=validate_compound_name,
        help="Name of the compound (e.g., 'GaAs', 'SiO2')."
    )
    parser.add_argument(
        "poscar_file",
        type=str,
        nargs='?',
        help="Path to the POSCAR file (required for input file generation)."
    )

    parser.add_argument(
        "--initialize-input",
        action="store_true",
        help="Initialize the project for input files."
    )

    parser.add_argument(
        "--project-config",
        type=str,
        help="Path to a custom JSON project configuration file."
    )

    parser.add_argument(
        "--config-type",
        type=str,
        default="default",
        choices=["default", "bands", "pdos", "wannier"],
        help="Type of configuration to use (default: 'default')."
    )

    args = parser.parse_args(argv[1:])
    is_input = args.initialize_input
    try:
        # Initialize and prepare project
        project = initialize_project(args.compound_name,
                                     args.project_config,
                                     args.config_type,
                                     args.poscar_file if is_input else None,
                                     is_input=is_input)

        print_header("Project Initialization Summary")
        print('\n')
        # Creating a table for project information
        info_table = Table(show_header=True, box=box.ROUNDED, title="Project Information", show_lines=True)
        info_table.add_column("Property", style=custom_theme.styles["info"])
        info_table.add_column("Value", style="green")

        info_table.add_row("Compound name", project.compound_name)
        info_table.add_row("Project directory", project.project_dir)
        info_table.add_row("Include stress", str(project.include_stress))
        if project.include_stress:
            info_table.add_row("Stress amounts", ", ".join(project.stress_amounts))
        info_table.add_row("Pseudo dir", project.pseudo_dir)
        info_table.add_row("Rel pseudo dir", project.rel_pseudo_dir)
        info_table.add_row("Elements", ", ".join(project.compound_data.element_names))
        info_table.add_row("Atomic labels", ", ".join(project.compound_data.atomic_labels))

        console.print(info_table, '\n')

        # Display paths in a separate table
        paths_table = Table(title="File Paths", show_header=True, show_lines=True)
        paths_table.add_column("Type", style="cyan")
        paths_table.add_column("Paths", style="green", overflow="fold")

        paths_dict = project.input_paths if is_input else project.output_paths
        for path_type, paths in paths_dict.items():
            paths_table.add_row(path_type, "\n".join(paths))

        console.print(paths_table)

    except ProjectInitializationError as e:
        print_error(f"Error during project initialization: {str(e)}")
        exit(1)

    except Exception as e:
        print_error(f"Unexpected Error: {str(e)}")
        exit(1)
