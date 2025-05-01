"""Functions for handling user input.

This module provides utility functions to interact with the user for input
related to plotting projected bands. It includes functions to select the type
of bands to plot, input strain amounts, and specify atomic states for projection.
"""

import os
import re
from typing import List, Tuple, Dict


def select_pseudopotentials(pseudo_files: List[str],
                            element_name: str,
                            relativistic: bool = False):
    """
    Prompts the user to select a pseudopotential file from a list.

    Args:
        pseudo_files (list): A list of pseudopotential file names.
        element_name (str): The name of the element.
        relativistic (bool, optional): Whether the pseudopotentials are relativistic.
                                     Defaults to False.

    Returns:
        str: The selected pseudopotential file name.
    """

    print(f"\nFinding {'relativistic' if relativistic else 'non-relativistic'} pseudopotential files for {element_name}:")
    if not pseudo_files:
        print(
            f"ERROR: No pseudopotentials found for {element_name}. Make sure they exist in the specified directory and rerun this script"
        )
        exit(1)
    else:
        print(f"Found the following pseudopotential files for {element_name}:")
        for i, filename in enumerate(pseudo_files):
            print(f"{i + 1}: {filename}")
        while True:
            try:
                selected_index = int(input("Which one do you want? Enter the number associated with it: ")) - 1
                return pseudo_files[selected_index]
            except (IndexError, ValueError):
                print("Invalid selection! Please select a valid number.")


def get_pseudopotential_files(element_names: List[str],
                              pseudo_path: str = "../Pseudopotentials",
                              *,
                              relativistic: bool = False,
                              rel_pseudo_path: str = None) -> Tuple[Dict, Dict] | Dict:
    """
    Gets the pseudopotential file paths from the user, searches for the files,
    and lets the user select the appropriate ones.

    Args:
        element_names (list): A list of element names in the compound.
        pseudo_path (str): Path of pseudopotential files
        relativistic (bool): Whether to get the relativistic pseudopotentials
        rel_pseudo_path (str): Path of relativistic pseudopotential files

    Returns:
        tuple: A tuple containing:
            - dict: A dictionary of selected non-relativistic pseudopotential file names.
            - dict: A dictionary of selected relativistic pseudopotential file names.
    """

    pseudo_list = {}
    rel_pseudo_list = {}

    # Get non-relativistic pseudopotentials
    pseudo_dir_path = os.path.abspath(pseudo_path)
    if os.path.exists(pseudo_dir_path):
        for element_name in element_names:
            pseudo_files = []
            pseudo_regex_pattern = rf"{element_name}[-\._].*\.upf"
            pseudo_regex_object = re.compile(pseudo_regex_pattern, re.IGNORECASE)
            for filename in os.listdir(pseudo_dir_path):
                if pseudo_regex_object.fullmatch(filename):
                    pseudo_files.append(filename)
            selected_pseudo = select_pseudopotentials(pseudo_files, element_name)
            pseudo_list[element_name] = selected_pseudo

    else:
        print(f"Directory {pseudo_dir_path} does not exist! Could not get the pseudopotential file path.")
        exit(1)

    # Get relativistic pseudopotentials
    if relativistic:

        rel_pseudo_dir_path = os.path.abspath(rel_pseudo_path)
        if os.path.exists(rel_pseudo_dir_path):

            for element_name in element_names:
                rel_pseudo_files = []
                pseudo_regex_pattern = rf"{element_name}[-\._].*\.upf"
                pseudo_regex_object = re.compile(pseudo_regex_pattern, re.IGNORECASE)
                for filename in os.listdir(rel_pseudo_dir_path):
                    if pseudo_regex_object.fullmatch(filename):
                        rel_pseudo_files.append(filename)
                selected_pseudo = select_pseudopotentials(
                    rel_pseudo_files, element_name, relativistic=True
                )
                rel_pseudo_list[element_name] = selected_pseudo
        else:
            print(f"Directory {pseudo_dir_path} does not exist! Could not get the pseudopotential file path.")
            exit(1)

        return pseudo_list, rel_pseudo_list

    else:
        return pseudo_list


def get_pbands_type():
    """
    Prompt the user to select the type of projected bands to plot.

    This function repeatedly asks the user whether they want to plot strained
    projected bands or normal projected bands until a valid input is provided.

    Returns:
        bool: True if the user chooses to plot strained projected bands, False otherwise.
    """
    while True:
        include_stress_input = input(
            'Do you want to plot strained projected bands instead? Type "yes" to plot strained projected bands and "no" to plot normal projected bands. '
        ).lower()

        if include_stress_input in ["yes", "no"]:
            return include_stress_input == "yes"
        else:
            print("Invalid input!")


def get_strain_amounts(is_input: bool = False) -> List[str] | None:
    """
    Prompt the user to input strain amounts for DFT calculations.

    This function repeatedly asks the user to provide a space-separated list of strain amounts
    in the format `1_<percent-of-stretch>`. It validates the input to ensure that at least one
    valid strain amount is provided and returns the list of strain amounts.

    Returns:
        list: A list of strings representing the strain amounts, e.g., ['1_10', '1_15', '1_20'].
    """

    if is_input:
        if input("Do you want to create strain analysis directories? (yes/no): ").strip().lower() == "yes":
            while True:
                stress_amount_list_input = input("""Enter the strain amounts in units of relaxed coordinates in the form 1_<percent-of-stretch>.
For example 1_30 means the coordinates are stretched by 30%. Provide a space separated list of DFT calculations with the specified stress amounts
(e.g., 1_10 1_15 1_20):
""")

                # Cleaning up user input and error handling
                stress_amount_list = [
                    amount for amount in stress_amount_list_input.split() if amount.strip()
                ]

                # List should not be empty
                if not stress_amount_list:
                    print("Error: No valid strain amounts provided.")
                else:
                    return stress_amount_list
        else:
            return None
    else:
        while True:
            stress_amount_list_input = input("""Enter the strain amounts in units of relaxed coordinates in the form 1_<percent-of-stretch>.
For example 1_30 means the coordinates are stretched by 30%. Provide a space separated list of DFT calculations with the specified stress amounts
(e.g., 1_10 1_15 1_20):
""")

            # Cleaning up user input and error handling
            stress_amount_list = [
                amount for amount in stress_amount_list_input.split() if amount.strip()
            ]

            # List should not be empty
            if not stress_amount_list:
                print("Error: No valid strain amounts provided.")
            else:
                return stress_amount_list


def get_atomic_states() -> List[Tuple[str, str]] | None:
    """
    Prepares and retrieves the atomic projection list for plotting projected bands.

    This function prompts the user to input atomic projections in the format
    <element name>-<orbital>, separated by spaces. It validates the input to ensure
    correctness and returns a list of atomic projections.

    Returns:
        list: A list of tuples where each tuple contains an element name (str) and
              an orbital type (str), e.g., [('O', 's'), ('C', 'p'), ('Fe', 'd')].
    """
    print("Preparing the atomic projection list for plotting projected bands...")

    supported_orbitals = ('s', 'p', 'd', 'pz', 'px', 'py', 'dz2', 'dxz', 'dyz', 'dx2y2', 'dxy')

    print(f"""
The supported orbitals are:
{', '.join(supported_orbitals)}
The projection list should be in pairs of <element name>-<orbital> separated by a single space.
Example usage: O-s C-p Fe-d
    """)

    # Loop to repeatedly prompt the user until valid input is provided
    while True:
        user_input = input("Enter the desired atomic orbitals you wish to project onto: ").strip()

        if not user_input:
            print("Input cannot be empty!")
            continue

        # Processing the user input and extracting atomic projection information
        atomic_projection_list = []
        for atomic_projection in user_input.split():

            # Validating the input format (must be in the form <element name>-<orbital>)
            if '-' not in atomic_projection:
                print("Invalid input format. Expected <element name>-<orbital>.")
                break

            element, orbital = atomic_projection.split('-')

            # Validating the element and orbital symbols
            if not element.isalpha():
                print("Invalid element symbol!")
                break

            if orbital not in supported_orbitals:
                print(f"Invalid orbital type! Supported types are: {', '.join(supported_orbitals)}")
                break

            atomic_projection_list.append((element, orbital))
        else:
            return atomic_projection_list
