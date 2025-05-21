"""Module for parsing Quantum ESPRESSO output files.

This module provides functions to extract information from Quantum ESPRESSO
output files, such as the number of bands, Fermi energy, number of atomic states,
and atomic state details. These functions are designed to handle specific file
formats and extract relevant data using regular expressions.
"""
import os
import re
import json
from typing import List, Tuple, Dict, Union

from ui.ui_helpers import print_info, print_success, print_error, console


def get_poscar_data(poscar_file: str) -> Tuple[List[str], List[str]]:
    """
    Reads the POSCAR file and extracts lattice vectors and atomic positions.

    Args:
        poscar_file (str): The path to the POSCAR file.

    Returns:
        tuple: A tuple containing:
            - list: A list of lattice vectors.
            - list: A list of atomic positions.
    """
    script_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    with open(os.path.join(script_root_dir, poscar_file), "r") as file:
        poscar_file_content = file.read()

    coordinates_regex_pattern = (
        r"(-?\d\d?\.\d+(?!\n))\s+(-?\d\d?\.\d+)\s+(-?\d\d?\.\d+)"
    )
    coordinates_regex_object = re.compile(coordinates_regex_pattern)
    coordinates_matches = coordinates_regex_object.finditer(poscar_file_content)

    lattice_vectors = []
    atomic_positions = []

    counter = 0
    for match in coordinates_matches:
        if counter < 3:
            lattice_vectors.append(
                f"{match.group(1):>20}    {match.group(2):>20}    {match.group(3):>20}"
            )
        else:
            atomic_positions.append(
                f"{match.group(1):>20}    {match.group(2):>20}    {match.group(3):>20}"
            )
        counter += 1

    return lattice_vectors, atomic_positions


def extract_band_number(file_path: str, compound_name: str, flag: str) -> int:
    """
    Extract the number of bands from a Quantum ESPRESSO bands calculation output file.

    Args:
        file_path (str): Path to the bands output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")

    Returns:
        int: Number of bands

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the band number cannot be extracted
    """
    print_info(f"Reading {compound_name}_bands{flag}.pw.out...")

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
            print_success(
                f"Band number extracted successfully. There are {number_of_bands} bands in this calculation.\n"
            )
            return number_of_bands

        except StopIteration:
            raise ValueError(f"Could not find band number information in {file_path}")

    except FileNotFoundError:
        print_error(
            f'File "{compound_name}_bands{flag}.pw.out" does not exist. Make sure the file name is correct or in the directory of the project.'
        )
        raise


def extract_fermi_energy(
    file_path: str, compound_name: str, flag: str, is_pdos: bool = False
) -> float:
    """
    Extract the Fermi energy from a Quantum ESPRESSO SCF calculation output file.

    Args:
        file_path (str): Path to the SCF output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")
        is_pdos (bool): Flag to indicate whether the file is for PDOS calculation

    Returns:
        float: Fermi energy in eV

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the Fermi energy cannot be extracted
    """
    print_info("Getting Fermi energy...")

    if not is_pdos:
        print_info(f"Reading {compound_name}_scf{flag}.pw.out...")

        try:
            with open(file_path, "r") as scf_output_file:
                scf_calculation_output = scf_output_file.read()

            # Getting fermi energy from the calculation output
            fermi_energy_regex_pattern = r"the Fermi energy is\s+(-?\d+\.\d+)"
            fermi_energy_regex_object = re.compile(fermi_energy_regex_pattern)
            fermi_energy_matches = fermi_energy_regex_object.finditer(
                scf_calculation_output
            )

            try:
                fermi_energy = float(next(fermi_energy_matches).group(1))
                print_success(
                    f"Fermi energy extracted successfully. Fermi energy is {fermi_energy} eV.\n"
                )
                return fermi_energy

            except StopIteration:
                raise ValueError(
                    f"Could not find Fermi energy information in {file_path}"
                )

        except FileNotFoundError:
            print_error(
                f'File "{compound_name}_scf{flag}.pw.out" does not exist. Make sure the file name is correct or in the directory of the project.'
            )
            raise

    else:
        print_info(f"Reading {compound_name}_nscf{flag}.pw.out...")

        try:
            with open(file_path, "r") as nscf_output_file:
                nscf_calculation_output = nscf_output_file.read()

            # Getting fermi energy from the calculation output
            fermi_energy_regex_pattern = r"the Fermi energy is\s+(-?\d+\.\d+)"
            fermi_energy_regex_object = re.compile(fermi_energy_regex_pattern)
            fermi_energy_matches = fermi_energy_regex_object.finditer(
                nscf_calculation_output
            )

            try:
                fermi_energy = float(next(fermi_energy_matches).group(1))
                print_success(
                    f"Fermi energy extracted successfully. Fermi energy is {fermi_energy} eV.\n"
                )
                return fermi_energy

            except StopIteration:
                raise ValueError(
                    f"Could not find Fermi energy information in {file_path}"
                )

        except FileNotFoundError:
            print_error(
                f'File "{compound_name}_nscf{flag}.pw.out" does not exist. Make sure the file name is correct or in the directory of the project.'
            )
            raise


def extract_number_of_atomic_states(
    file_path: str, compound_name: str, flag: str
) -> int:
    """
    Extract the number of atomic states from a Quantum ESPRESSO KPDOS calculation output file.

    Args:
        file_path (str): Path to the kpdos output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")

    Returns:
        int: Number of atomic states

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the number of atomic states cannot be extracted
    """
    print_info(f"Reading {compound_name}{flag}.kpdos.out...")

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
            print_success(
                f"Number of atomic states extracted successfully. There are {number_of_atomic_states} atomic states in this calculation.\n"
            )
            return number_of_atomic_states

        except StopIteration:
            raise ValueError(
                f"Could not find number of atomic states information in {file_path}"
            )

    except FileNotFoundError:
        print_error(
            f'File "{compound_name}{flag}.kpdos.out" does not exist. Make sure the file name is correct or in the directory of the project.'
        )
        raise


def extract_atomic_states_info(
    file_path: str,
    compound_name: str,
    flag: str,
    atom: str,
    orbital: str,
    is_pdos: bool = False,
) -> (
    Dict[str, Dict[str, Union[List[int], List[float]]]]
    | Dict[str, List[Tuple[int, int]]]
):
    """
    Extract the atomic states info from a Quantum ESPRESSO KPDOS calculation output file.

    Args:
        file_path (str): Path to the kpdos output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")
        atom (str): Atomic symbol
        orbital (str): Orbital type (e.g., "s", "p", "d")
        is_pdos (bool): Flag to indicate whether to extract PDOS information

    Returns:
        dict: Dictionary containing the indices and orbital weights for the specified atom and orbital

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the atomic state cannot be extracted
    """
    console.rule(f"Getting atomic projection {atom}-{orbital}")

    if not is_pdos:
        try:
            with open(file_path, "r") as kpdos_output_file:
                kpdos_calculation_output = kpdos_output_file.read()

            orbital_info = json.load(open("data/orbital_info.json", "r"))
            # Orbitals with the same contribution
            same_orbitals = {
                "px": "px+py",
                "py": "px+py",
                "dxz": "dxz+dyz",
                "dyz": "dxz+dyz",
                "dx2y2": "dx2y2+dxy",
                "dxy": "dx2y2+dxy",
            }

            projection_indices_list = []

            # Validating the orbital exists in orbital info file
            if orbital not in orbital_info:
                raise ValueError(
                    f"The orbital '{orbital}' is not defined in 'orbital_info.json'. Please check the file."
                )

            # Getting the index of all atomic states given by user input
            for orbital_number in orbital_info[orbital]["orbital_numbers"]:
                atomic_state_regex_pattern = rf"state #\s+(\d+): atom\s+\d+ \({atom}\s+\), wfc\s+\d+ \({orbital_number}\)"
                atomic_state_regex_object = re.compile(atomic_state_regex_pattern)

                projection_indices_list.extend(
                    [
                        int(atomic_state.group(1))
                        for atomic_state in atomic_state_regex_object.finditer(
                            kpdos_calculation_output
                        )
                    ]
                )
            projection_indices_list.sort()

            if orbital in same_orbitals:
                key = f"{atom}-{same_orbitals[orbital]}"
            else:
                key = f"{atom}-{orbital}"

            if not projection_indices_list:
                raise ValueError(
                    f"Could not find atomic projection {atom}-{orbital} in {file_path}"
                )

            return {
                key: {
                    "indices": projection_indices_list,
                    "coefficients": orbital_info[orbital]["orbital_coefficients"],
                }
            }

        except ValueError as e:
            print_error(f"There was an error in extracting the atomic projection information.")
            raise

        except FileNotFoundError:
            print_error(
                f'File "{compound_name}{flag}.kpdos.out" does not exist. Make sure the file name is correct or in the directory of the project.'
            )
            raise

    else:
        try:
            orbital_lookup = {
                "s": "0",
                "p": "1",
                "d": "2",
            }  # Map orbital numbers to types

            if orbital not in orbital_lookup:
                raise ValueError(
                    f"The orbital '{orbital}' is not defined in the orbital lookup."
                )

            with open(file_path, "r") as pdos_output_file:
                pdos_calculation_output = pdos_output_file.read()

            atomic_state_regex_pattern = (
                rf"state #\s+\d+: atom\s+(?P<atomic_index>\d+) \({atom}\s+\),"
                rf" wfc\s+(?P<wfc_num>\d+) \(l=({orbital_lookup[orbital]}).*\)"
            )
            atomic_state_regex_object = re.compile(atomic_state_regex_pattern)
            atomic_state_matches = atomic_state_regex_object.finditer(
                pdos_calculation_output
            )

            projection_info_list = [(int(match.group("atomic_index")), int(match.group("wfc_num")))
                                 for match in atomic_state_matches]


            key = f"{atom}-{orbital}"
            return {
                key: {
                    "atomic_indices": [info[0] for info in projection_info_list],
                    "wavefunction_numbers": [info[1] for info in projection_info_list],
                }
            }

        except ValueError:
            print_error("There was an error in extracting the atomic projection information.")
            raise

        except FileNotFoundError:
            print_error(
                f'File "{compound_name}{flag}.pdos.out" does not exist. Make sure the file name is correct or in the directory of the project.'
            )
            raise


def extract_wannier_parameters(
    file_path: str, compound_name: str, flag: str
) -> Tuple[float, float]:
    """Extract Wannier calculation parameters from NSCF output file.

    Args:
        file_path (str): Path to the NSCF Wannier output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")

    Returns:
        tuple: (alat_parameter, fermi_energy)

    Raises:
        ValueError: If parameters cannot be extracted
        FileNotFoundError: If the file does not exist
    """
    print_info(f"Reading {compound_name}_nscf_wannier{flag}.pw.out...")

    with open(file_path, "r") as f:
        content = f.read()

    # Extract alat parameter
    alat_match = re.search(r"celldm\(1\)=\s+(\d\.\d+)", content)
    if not alat_match:
        raise ValueError("Alat parameter not found in NSCF output")
    alat = float(alat_match.group(1)) * 0.529177  # Convert bohr to angstrom

    # Extract Fermi energy
    fermi_match = re.search(r"the Fermi energy is\s+(-?\d\.\d+)", content)
    if not fermi_match:
        raise ValueError("Fermi energy not found in NSCF output")
    fermi_energy = float(fermi_match.group(1))

    print_success("Parameters extracted successfully:")
    print_info(f"Alat parameter: {alat} Å")
    print_info(f"Fermi energy: {fermi_energy} eV\n")

    return alat, fermi_energy
