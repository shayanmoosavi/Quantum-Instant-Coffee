"""Functions for handling user input.

This module provides utility functions to interact with the user for input
related to plotting projected bands. It includes functions to select the type
of bands to plot, input strain amounts, and specify atomic states for projection.
"""

import os
import re
from typing import List, Tuple, Dict

from ui.ui_helpers import *


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

    header_text = f"{'Relativistic' if relativistic else 'Non-relativistic'} pseudopotentials for [bold]{element_name}[/bold]"
    print_header(header_text)

    if not pseudo_files:
        print_error(f"ERROR: No pseudopotentials found for {element_name}. Make sure they exist in the specified directory and rerun this script.")
        exit(1)

    print_list(f"Available Pseudopotentials for {element_name}", pseudo_files)

    while True:
        try:
            selected_index = int(prompt_input("Which one do you want? Enter the number: ")) - 1
            return pseudo_files[selected_index]
        except (IndexError, ValueError):
            print_warning("Invalid selection! Please enter a valid number from the list.")


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
        print_info(f"Searching for pseudopotential files in: {pseudo_dir_path}")

        for element_name in element_names:
            pseudo_files = []
            pseudo_regex_pattern = rf"{element_name}[-\._].*\.upf"
            pseudo_regex_object = re.compile(pseudo_regex_pattern, re.IGNORECASE)
            for filename in os.listdir(pseudo_dir_path):
                if pseudo_regex_object.fullmatch(filename):
                    pseudo_files.append(filename)
            selected_pseudo = select_pseudopotentials(pseudo_files, element_name)
            pseudo_list[element_name] = selected_pseudo

        # Get relativistic pseudopotentials
        if relativistic:

            rel_pseudo_dir_path = os.path.abspath(rel_pseudo_path)
            if os.path.exists(rel_pseudo_dir_path):

                print_info(f"\nSearching for relativistic pseudopotential files in: {rel_pseudo_dir_path}\n")

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

                return pseudo_list, rel_pseudo_list

            else:
                print_error(
                    f"ERROR: Directory {pseudo_dir_path} does not exist! Could not get the pseudopotential file path.")
                exit(1)

        else:
            return pseudo_list
    else:
        print_error(f"ERROR: Directory {pseudo_dir_path} does not exist! Could not get the pseudopotential file path.")
        exit(1)


def get_pbands_type():
    """
    Prompt the user to select the type of projected bands to plot.

    This function repeatedly asks the user whether they want to plot strained
    projected bands or normal projected bands until a valid input is provided.

    Returns:
        bool: True if the user chooses to plot strained projected bands, False otherwise.
    """
    while True:
        include_stress_input = prompt_input(
            'Do you want to plot strained projected bands instead? Type "y" to plot strained projected bands and "n" to plot normal projected bands. '
        ).strip().lower()

        if include_stress_input in ["y", "n"]:
            return include_stress_input == "y"
        else:
            print_warning("Invalid input! Please type 'y' or 'n'.")


def get_strain_amounts(is_input: bool = False) -> List[str] | None:
    """
    Prompt the user to input strain amounts for DFT calculations.

    This function repeatedly asks the user to provide a space-separated list of strain amounts
    in the format `1_<percent-of-stretch>`. It validates the input to ensure that at least one
    valid strain amount is provided and returns the list of strain amounts.

    Returns:
        list: A list of strings representing the strain amounts, e.g., ['1_10', '1_15', '1_20'].
    """

    def prompt_strain_input():
        print_info("""Enter the strain amounts in units of relaxed coordinates in the form 1_<percent-of-stretch>.
        For example 1_30 means the coordinates are stretched by 30%. Provide a space separated list of DFT calculations with the specified stress amounts
        (e.g., 1_10 1_15 1_20)
        """)
        user_input = prompt_input("Strain amounts: ")

        # Cleaning up user input and error handling
        return [
            amount for amount in user_input.split() if amount.strip()
        ]

    if is_input:
        if prompt_input("Do you want to create strain analysis directories? (y/n): ").strip().lower() == "y":
            while True:

                stress_amount_list = prompt_strain_input()

                # List should not be empty
                if not stress_amount_list:
                    print_error("Error: No valid strain amounts provided.")
                else:
                    return stress_amount_list
        else:
            return None
    else:
        while True:

            stress_amount_list = prompt_strain_input()

            # List should not be empty
            if not stress_amount_list:
                print_error("Error: No valid strain amounts provided.")
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
    print_header("Atomic Projections")
    print_info("Preparing the atomic projection list for plotting projected bands...")

    supported_orbitals = ('s', 'p', 'd', 'pz', 'px', 'py', 'dz2', 'dxz', 'dyz', 'dx2y2', 'dxy')

    print_info(f"""
Supported orbitals:
{', '.join(supported_orbitals)}
Format: <element_name>-<orbital> separated by a single space.
Example: O-s C-p Fe-d
    """, highlight=False)

    # Loop to repeatedly prompt the user until valid input is provided
    while True:
        user_input = prompt_input("Enter the desired atomic orbitals you wish to project onto: ").strip()

        if not user_input:
            print_warning("Input cannot be empty!")

        # Processing the user input and extracting atomic projection information
        atomic_projection_list = []
        for atomic_projection in user_input.split():

            # Validating the input format (must be in the form <element name>-<orbital>)
            if '-' not in atomic_projection:
                print_warning("Invalid input format. Expected <element_name>-<orbital>.")
                break

            element, orbital = atomic_projection.split('-')

            # Validating the element and orbital symbols
            if not element.isalpha():
                print_warning("Invalid element symbol!")
                break

            if orbital not in supported_orbitals:
                print_warning(f"Invalid orbital type! Supported types are: {', '.join(supported_orbitals)}")
                break

            atomic_projection_list.append((element, orbital))
        else:
            return atomic_projection_list
