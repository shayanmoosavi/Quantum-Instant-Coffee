"""Module for collecting data from Quantum ESPRESSO output files.

This module provides functions and classes to extract and process data from Quantum ESPRESSO output files.
It includes functionality for handling spin-orbit coupling (SOC), collecting DFT data, and generating projected bands.
"""

import os
from sys import argv
from file_parser import *
from init_project import initialize_project
from input_handler import get_atomic_states
from models import DFTInfo
from subprocess import CalledProcessError, run
from project_setup import ProjectInitializationError


class SpinOrbitHandler:
    """
    A class to handle spin-orbit coupling (SOC) related logic, including skipping SOC cases
    and managing errors during data collection from Quantum ESPRESSO output files.

    Attributes:
        skip_soc (bool): Indicates whether SOC cases should be skipped automatically.
    """

    def __init__(self, skip_soc=False):
        """
        Initializes the SpinOrbitHandler with the option to skip SOC cases.

        Args:
            skip_soc (bool): Whether to skip SOC cases. Defaults to False.
        """
        self.skip_soc = skip_soc

    def should_skip(self, flag):
        """
        Determines if a given case should be skipped based on the SOC flag.

        Args:
            flag (str): The flag indicating whether the case involves SOC (e.g., "_soc").

        Returns:
            bool: True if the case should be skipped, False otherwise.
        """
        return self.skip_soc and flag == "_soc"

    def handle_error(self, flag):
        """
        Handles errors encountered during data collection. For SOC cases, it provides
        the user with the option to skip the case or exit the program. For non-SOC cases,
        the program exits immediately.

        Args:
            flag (str): The flag indicating whether the case involves SOC (e.g., "_soc").

        Returns:
            bool: True if the SOC case is skipped, False otherwise.

        Raises:
            SystemExit: If the user chooses not to skip the SOC case or if the error is
                        not related to SOC.
        """
        if flag != "_soc":
            exit(1) # Exit immediately for non spin-orbit cases

        if self.skip_soc:
            print("Spin-orbit was set to be skipped. Continuing...")
            return True

        skip_soc_input = input(
            'Do you want to skip spin-orbit case? Enter "yes" if you want to skip spin-orbit or "no" to quit the program: '
        ).lower()

        if skip_soc_input == "no":
            exit(1)
        return True

def collect_dft_data(paths, compound_name, flag, extractor_func, atom = None, orbital = None):
    """
    Collect data from Quantum ESPRESSO output files using a specified extractor function.

    Args:
        paths (dict): Dictionary containing file paths.
        compound_name (str): Name of the compound being analyzed.
        flag (str): Suffix for the file name (e.g., "_soc" or "").
        extractor_func (function): Function used to extract specific data from the file.
        atom (str): Atomic symbol
        orbital (str): Orbital type (e.g., "s", "p", "d")

    Returns:
        tuple: A tuple containing:
            - data (any): The extracted data if successful, or None if an error occurs.
            - success (bool): True if data extraction was successful, False otherwise.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the data cannot be extracted from the file or one of atom or orbital is not None.
    """
    try:
        # atom and orbital should either be both None or both not None
        match (atom is None, orbital is None):

            case (True, True):
                data = extractor_func(paths, compound_name, flag)
                return data, True

            case (True, False) | (False, True):
                raise ValueError(
                    """Both atom and orbital should be either None or not None.
                    If you want to extract atomic states, please provide both atom and orbital."""
                )

            case (False, False):
                data = extractor_func(paths, compound_name, flag, atom, orbital)
                return data, True

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return None, False


def collect_band_numbers(paths, compound_name, spin_orbit_flag, skip_soc=False):
    """
    Collect band numbers from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flag (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: List of band numbers
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    number_of_bands_list = []

    for path, flag in zip(paths["pw_bands_output_paths"], spin_orbit_flag):
        if soc_handler.should_skip(flag):
            continue

        data, success = collect_dft_data(path, compound_name, flag, extract_band_number)

        if not success:
            if soc_handler.handle_error(flag):
                return number_of_bands_list
        else:
            number_of_bands_list.append(data)

    return number_of_bands_list


def collect_fermi_energies(paths, compound_name, spin_orbit_flag, skip_soc=False):
    """
    Collect Fermi energies from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flag (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: List of Fermi energies
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    fermi_energy_list = []

    for path, flag in zip(paths["scf_output_paths"], spin_orbit_flag):

        if soc_handler.should_skip(flag):
            continue

        data, success = collect_dft_data(path, compound_name, flag, extract_fermi_energy)

        if not success:
            if soc_handler.handle_error(flag):
                return fermi_energy_list
        else:
            fermi_energy_list.append(data)

    return fermi_energy_list

def collect_number_of_atomic_states(paths, compound_name, spin_orbit_flag, skip_soc=False):
    """
    Collect the number of atomic states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flag (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: List of number of atomic states
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    number_of_atomic_states_list = []

    for path, flag in zip(paths["kpdos_output_paths"], spin_orbit_flag):
        if soc_handler.should_skip(flag):
            continue

        data, success = collect_dft_data(path, compound_name, flag, extract_number_of_atomic_states)

        if not success:
            if soc_handler.handle_error(flag):
                return number_of_atomic_states_list
        else:
            number_of_atomic_states_list.append(data)

    return number_of_atomic_states_list


def collect_atomic_states_info(paths, compound_name, spin_orbit_flag, skip_soc=False):
    """
    Collect the atomic info states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flag (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: A list of dictionaries containing the indices and orbital weights of each atomic state
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    atomic_states_info_list = []

    atomic_projection_list = get_atomic_states()

    for path, flag in zip(paths["kpdos_output_paths"], spin_orbit_flag):

        atomic_states_info = {}
        if soc_handler.should_skip(flag):
            continue

        for atom, orbital in atomic_projection_list:
            data, success = collect_dft_data(path, compound_name, flag, extract_atomic_states_info, atom, orbital)

            if not success:
                if soc_handler.handle_error(flag):
                    break
            else:
                atomic_states_info.update(data)

        atomic_states_info_list.append(atomic_states_info)

    return atomic_states_info_list


def run_awk_script(number_of_atomic_states, fermi_energy, kpdos_output_dir, projbands_dir):
    """
    Execute the AWK script to generate projected bands data.

    Args:
        number_of_atomic_states (int): Number of atomic states
        fermi_energy (float): Fermi energy value
        kpdos_output_dir (str): KPDOS output path
        projbands_dir (str): Path to generate the projbands file

    Raises:
        CalledProcessError: If the AWK script execution fails
    """
    print("Calculating projected bands...")

    awk_command = (
        f"awk -v firststate=1 "
        f"-v laststate={number_of_atomic_states} "
        f"-v ef={fermi_energy} "
        f"-f ./projwfc_to_bands.awk {kpdos_output_dir} > {projbands_dir}"
    )

    run(awk_command, shell=True, check=True, capture_output=True)


def generate_projected_bands(paths, number_of_atomic_states_list, fermi_energy_list):
    """
    Generate projected bands data if not already present.

    This function checks if the projected bands file already exists. If it does not,
    it runs an AWK script to generate the file. The function tracks the success or
    failure of the generation process for each file.

    Args:
        paths (dict): A dictionary containing file paths, including:
            - "kpdos_output_paths" (list): List of KPDOS output file paths.
            - "projbands_paths" (list): List of paths where projbands files should be generated.
        number_of_atomic_states_list (list): A list of integers representing the number of atomic states for each calculation output
        fermi_energy_list (list): A list of floats representing the Fermi energy values for each calculation output.
    Returns:
        list: A list of boolean values indicating the success (True) or failure (False)
              of the projected bands generation for each file.
    """

    # List to track whether the projbands generation was successful for each file
    projbands_generation_success_list = []

    # Iterating over the KPDOS output paths and corresponding projbands paths
    for (projbands_dir, kpdos_output_dir,
         number_of_atomic_states, fermi_energy) in zip(
        paths["projbands_paths"], paths["kpdos_output_paths"],
        number_of_atomic_states_list, fermi_energy_list
    ):

        # Checking if the projbands file already exists
        if os.path.exists(projbands_dir):
            print(f"File {projbands_dir} already exists!")
            projbands_generation_success_list.append(True)
            continue

        try:
            # Running the AWK script to generate the projbands file
            run_awk_script(number_of_atomic_states, fermi_energy, kpdos_output_dir, projbands_dir)
            print("Projected bands calculation completed successfully.")
            projbands_generation_success_list.append(True)

        except CalledProcessError as e:
            # Handling errors during the AWK script execution
            print("Error calculating projected bands:")
            print(e.stderr.decode("utf-8"))
            projbands_generation_success_list.append(False)

    return projbands_generation_success_list


def prepare_dft_info(project):
    """
    Prepare DFT (Density Functional Theory) information by extracting data from Quantum ESPRESSO output files.

    Args:
        project (ProjectSetup):

    Returns:
        ProjectSetup:
    """

    # Determine spin_orbit_flags based on project configuration
    spin_orbit_flags = (
        ["" for _ in range(len(project.stress_amounts) + 1)]
        if project.include_stress
        else ["", "_soc"]
    )

    # # Extracting band numbers
    number_of_bands_list = collect_band_numbers(
        project.output_paths,
        project.compound_name,
        spin_orbit_flags,
        project.skip_soc
    )

    # Extracting Fermi energies
    fermi_energies = collect_fermi_energies(
        project.output_paths,
        project.compound_name,
        spin_orbit_flags,
        project.skip_soc
    )

    # Extracting number of atomic states
    number_of_atomic_states_list = collect_number_of_atomic_states(
        project.output_paths,
        project.compound_name,
        spin_orbit_flags,
        project.skip_soc
    )

    # Extracting atomic states information
    atomic_states_info_list = collect_atomic_states_info(
        project.output_paths,
        project.compound_name,
        spin_orbit_flags,
        project.skip_soc
    )

    dft_info = DFTInfo(
        number_of_bands=number_of_bands_list,
        fermi_energies=fermi_energies,
        number_of_atomic_states=number_of_atomic_states_list,
        atomic_states_info=atomic_states_info_list,
        spin_orbit_flags=spin_orbit_flags
    )

    # Generate projected bands
    success = generate_projected_bands(
        project.output_paths,
        dft_info.number_of_atomic_states,
        dft_info.fermi_energies
    )

    if not all(success):
        raise ProjectInitializationError("Some projbands files were not generated successfully.")

    # Add DFT info to project
    project.add_dft_info(dft_info)
    return project


# Test to ensure the module works as expected
if __name__ == "__main__":
    """
    Main entry point for testing the module.

    This script validates that the prepare_dft_info has executed successfully and prints the extracted 
    information if successful.
    """

    is_input = len(argv) == 3

    project = initialize_project(argv, is_input)
    prepare_dft_info(project)

    print("DFT information prepared successfully.\n")
    if project.include_stress:
        for stress_amount, number_of_bands, fermi_energy, number_of_atomic_states, atomic_states_info in zip(
                [None] + project.stress_amounts,
                project.dft_info.number_of_bands,
                project.dft_info.fermi_energies,
                project.dft_info.number_of_atomic_states,
                project.dft_info.atomic_states_info
        ):
            print(f"\nStress amount: {stress_amount}")
            print(f"Number of bands: {number_of_bands}")
            print(f"Fermi energy: {fermi_energy}")
            print(f"Number of atomic states: {number_of_atomic_states}")
            print("\nAtomic states info:")
            for atomic_state, info in atomic_states_info.items():
                print(f"{atomic_state}: {info}")

    else:
        for number_of_bands, fermi_energy, number_of_atomic_states, atomic_states_info, flag in zip(
                project.dft_info.number_of_bands,
                project.dft_info.fermi_energies,
                project.dft_info.number_of_atomic_states,
                project.dft_info.atomic_states_info,
                ["", "(SOC)"]
        ):
            print(f"Number of bands {flag}: {number_of_bands}")
            print(f"Fermi energy {flag}: {fermi_energy}")
            print(f"Number of atomic states {flag}: {number_of_atomic_states}")
            print(f"\nAtomic states info {flag}:")
            for atomic_state, info in atomic_states_info.items():
                print(f"{atomic_state}: {info}")
