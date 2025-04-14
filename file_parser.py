"""Module for parsing Quantum ESPRESSO output files."""

import re


def extract_band_number(file_path, compound_name, flag):
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


def extract_fermi_energy(file_path, compound_name, flag):
    """
    Extract the Fermi energy from a Quantum ESPRESSO SCF calculation output file.

    Args:
        file_path (str): Path to the SCF output file
        compound_name (str): Name of the compound
        flag (str): Suffix for the file name (e.g., "_soc" or "")

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
