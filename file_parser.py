"""Module for parsing Quantum ESPRESSO output files.

This module provides functions to extract information from Quantum ESPRESSO
output files, such as the number of bands, Fermi energy, number of atomic states,
and atomic state details. These functions are designed to handle specific file
formats and extract relevant data using regular expressions.
"""

import re
import json


def get_poscar_data(poscar_file):
    """
    Reads the POSCAR file and extracts lattice vectors and atomic positions.

    Args:
        poscar_file (str): The path to the POSCAR file.

    Returns:
        tuple: A tuple containing:
            - list: A list of lattice vectors.
            - list: A list of atomic positions.
    """

    with open(poscar_file, "r") as file:
        poscar_file_content = file.read()

    coordinates_regex_pattern = r"(-?\d\d?\.\d+(?!\n))\s+(-?\d\d?\.\d+)\s+(-?\d\d?\.\d+)"
    coordinates_regex_object = re.compile(coordinates_regex_pattern)
    coordinates_matches = coordinates_regex_object.finditer(poscar_file_content)

    lattice_vectors = []
    atomic_positions = []

    counter = 0
    for match in coordinates_matches:
        if counter < 3:
            lattice_vectors.append(f"{match.group(1):>13}    {match.group(2):>13}    {match.group(3):>13}")
        else:
            atomic_positions.append(f"{match.group(1):>13}    {match.group(2):>13}    {match.group(3):>13}")
        counter += 1

    return lattice_vectors, atomic_positions


def extract_band_number(file_path, compound_name, flag, atom=None, orbital=None):
    """
    Extract the number of bands from a Quantum ESPRESSO bands calculation output file.

    Args:
        file_path (str): Path to the bands output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")
        atom: Added for function signature compatibility
        orbital: Added for function signature compatibility

    Returns:
        int: Number of bands

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the band number cannot be extracted
    """
    print(f"Reading {compound_name}_bands{flag}.pw.out...")

    try:
        with open(file_path, "r") as band_output_file:
            bands_calculation_output = band_output_file.read()

        # Getting the number of calculated bands from the calculation output
        band_number_regex_pattern = r"number of Kohn-Sham states=\s+(\d+)"
        band_number_regex_object = re.compile(band_number_regex_pattern)
        band_number_matches = band_number_regex_object.finditer(
            bands_calculation_output
        )

        try:
            number_of_bands = int(next(band_number_matches).group(1))
            print(
                f"Band number extracted successfully. There are {number_of_bands} bands in this calculation.\n"
            )
            return number_of_bands

        except StopIteration:
            raise ValueError(f"Could not find band number information in {file_path}")

    except FileNotFoundError:
        print(
            f'File "{compound_name}_bands{flag}.pw.out" does not exist. Make sure the file name is correct or in the directory of the project.'
        )
        raise


def extract_fermi_energy(file_path, compound_name, flag, atom=None, orbital=None):
    """
    Extract the Fermi energy from a Quantum ESPRESSO SCF calculation output file.

    Args:
        file_path (str): Path to the SCF output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")
        atom: Added for function signature compatibility
        orbital: Added for function signature compatibility

    Returns:
        float: Fermi energy in eV

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the Fermi energy cannot be extracted
    """
    print("Getting Fermi energy...")
    print(f"Reading {compound_name}_scf{flag}.pw.out...")

    try:
        with open(file_path, "r") as scf_output_file:
            scf_calculation_output = scf_output_file.read()

        # Getting fermi energy from the calculation output
        fermi_energy_regex_pattern = r"the Fermi energy is\s+(-?\d+\.\d+)"
        fermi_energy_regex_object = re.compile(fermi_energy_regex_pattern)
        fermi_energy_matches = fermi_energy_regex_object.finditer(scf_calculation_output)

        try:
            fermi_energy = float(next(fermi_energy_matches).group(1))
            print(f"Fermi energy extracted successfully. Fermi energy is {fermi_energy} eV.\n")
            return fermi_energy

        except StopIteration:
            raise ValueError(f"Could not find Fermi energy information in {file_path}")

    except FileNotFoundError:
        print(
            f'File "{compound_name}_scf{flag}.pw.out" does not exist. Make sure the file name is correct or in the directory of the project.')
        raise


def extract_number_of_atomic_states(file_path, compound_name, flag, atom=None, orbital=None):
    """
    Extract the number of atomic states from a Quantum ESPRESSO KPDOS calculation output file.

    Args:
        file_path (str): Path to the kpdos output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")
        atom: Added for function signature compatibility
        orbital: Added for function signature compatibility

    Returns:
        int: Number of atomic states

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the number of atomic states cannot be extracted
    """
    print(f"Reading {compound_name}{flag}.kpdos.out...")

    try:
        with open(file_path, "r") as kpdos_output_file:
            kpdos_calculation_output = kpdos_output_file.read()

        # Getting the number of atomic states from the calculation output
        atomic_states_regex_pattern = r"natomwfc =\s+(\d+)"
        atomic_states_regex_object = re.compile(atomic_states_regex_pattern)
        atomic_states_matches = atomic_states_regex_object.finditer(
            kpdos_calculation_output
        )

        try:
            number_of_atomic_states = int(next(atomic_states_matches).group(1))
            print(
                f"Number of atomic states extracted successfully. There are {number_of_atomic_states} atomic states in this calculation.\n"
            )
            return number_of_atomic_states

        except StopIteration:
            raise ValueError(
                f"Could not find number of atomic states information in {file_path}"
            )

    except FileNotFoundError:
        print(
            f'File "{compound_name}{flag}.kpdos.out" does not exist. Make sure the file name is correct or in the directory of the project.'
        )
        raise


def extract_atomic_states_info(file_path, compound_name, flag, atom, orbital):
    """
    Extract the atomic states info from a Quantum ESPRESSO KPDOS calculation output file.

    Args:
        file_path (str): Path to the kpdos output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")
        atom (str): Atomic symbol
        orbital (str): Orbital type (e.g., "s", "p", "d")

    Returns:
        dict: Dictionary containing the indices and orbital weights for the specified atom and orbital

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the atomic state cannot be extracted
    """
    print(f"Getting atomic state {atom}-{orbital}...")

    try:
        with open(file_path, "r") as kpdos_output_file:
            kpdos_calculation_output = kpdos_output_file.read()

        orbital_info = json.load(open("orbital_info.json", "r"))

        # Orbitals with the same contribution
        same_orbitals = {
            "px": "px+py",
            "py": "px+py",
            "dxz": "dxz+dyz",
            "dyz": "dxz+dyz",
            "dx2y2": "dx2y2+dxy",
            "dxy": "dx2y2+dxy"
        }

        projection_indices_list = []

        # Validating the orbital exists in orbital info file
        if orbital not in orbital_info:
            raise ValueError(
                f"The orbital '{orbital}' is not defined in 'orbital_info.json'. Please check the file.")

        # Getting the index of all atomic states given by user input
        for orbital_number in orbital_info[orbital]['orbital_numbers']:
            atomic_state_regex_pattern = rf"state #\s+(\d+): atom\s+\d+ \({atom}\s+\), wfc\s+\d+ \({orbital_number}\)"
            atomic_state_regex_object = re.compile(atomic_state_regex_pattern)

            projection_indices_list.extend([int(atomic_state.group(1)) for atomic_state
                                       in atomic_state_regex_object.finditer(kpdos_calculation_output)])
        projection_indices_list.sort()

        if orbital in same_orbitals:
            key = f"{atom}-{same_orbitals[orbital]}"
        else:
            key = f"{atom}-{orbital}"

        if not projection_indices_list:
            raise ValueError(
                f"Could not find atomic state information for {atom}-{orbital} in {file_path}"
            )

        return {
            key: {
                "indices": projection_indices_list,
                "coefficients": orbital_info[orbital]["orbital_coefficients"]
            }
        }

    except ValueError:
        print("There was an error in extracting the atomic state information.")
        raise

    except FileNotFoundError:
        print(
            f'File "{compound_name}{flag}.kpdos.out" does not exist. Make sure the file name is correct or in the directory of the project.'
        )
        raise