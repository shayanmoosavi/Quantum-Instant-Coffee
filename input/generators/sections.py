"""Quantum ESPRESSO Input File Sections Generator

This module provides functions for generating sections of Quantum ESPRESSO input files,
including the &CONTROL, &SYSTEM, &ELECTRONS, ATOMIC_SPECIES, ATOMIC_POSITIONS,
and CELL_PARAMETERS sections. It also defines a custom exception,
`InputGenerationError`, for handling errors during input file generation.
"""
import os
from typing import List, Dict


class InputGenerationError(Exception):
    """Custom exception for input file generation errors."""
    pass


def generate_control_section(
        calculation_type: str,
        pseudo_dir: str,
        project_dir: str,
        compound_name: str,
        *,
        etot_conv_thr: float = 1e-8,
        forc_conv_thr: float = 1e-6,
        relativistic: bool = False,
) -> str:
    """
    Generates the &CONTROL section of the input file.

    Args:
        calculation_type (str): The type of calculation (e.g., 'vc-relax', 'scf').
        pseudo_dir (str): Path to the pseudopotential directory.
        project_dir (str): Path to the project directory.
        compound_name (str): Name of the compound.
        etot_conv_thr (float, optional): Energy convergence threshold. Defaults to 1e-8.
        forc_conv_thr (float, optional): Force convergence threshold. Defaults to 1e-6.
        relativistic (bool, optional): Whether the calculation is relativistic.
                                     Defaults to False.

    Returns:
        str: The &CONTROL section of the input file.
    """
    pseudo_dir_path = os.path.join(
        "../../" if relativistic else "../", os.path.relpath(pseudo_dir, project_dir))

    return f"""&CONTROL
    calculation      = '{calculation_type}'
    outdir           = './out'
    pseudo_dir       = '{pseudo_dir_path}'
    prefix           = '{compound_name}'
    verbosity        = 'high'
    etot_conv_thr    = {etot_conv_thr}
    forc_conv_thr    = {forc_conv_thr}
    tprnfor          = .true.
    tstress          = .true.
/
"""


def generate_system_section(
        number_of_atoms: int,
        atom_types: int,
        *,
        ecutwfc: int = 50,
        ecutrho: int = 500,
        number_of_bands: int = None,
        relativistic: bool = False,
) -> str:
    """
    Generates the &SYSTEM section of the input file.

    Args:
        number_of_atoms (int): The number of atoms in the system.
        atom_types (int): The number of distinct atom types.
        ecutwfc (int, optional): Plane-wave cutoff energy in Ry. Defaults to 50.
        ecutrho (int, optional): Charge density cutoff energy in Ry. Defaults to 500.
        number_of_bands (int, optional): The number of bands. Required for NSCF and Bands calculations.
                                        Defaults to None.
        relativistic (bool, optional): Whether the calculation is relativistic.
                                     Defaults to False.

    Returns:
        str: The &SYSTEM section of the input file.
    """

    system_section = f"""&SYSTEM
    ibrav            = 0
    nat              = {number_of_atoms}
    ntyp             = {atom_types}
    ecutwfc          = {ecutwfc}
    ecutrho          = {ecutrho}
"""

    if number_of_bands is not None:
        system_section += f"    nbnd             = {number_of_bands}\n"
    if relativistic:
        system_section += """    lspinorb         = .true.
    noncolin         = .true.
/
"""
    else:
        system_section += "/\n"

    return system_section


def generate_electrons_section(
        *,
        relativistic: bool = False,
        conv_thr: float = 1e-9,
        electron_maxstep: int = 500
) -> str:
    """
    Generates the &ELECTRONS section of the input file.

    Args:
        relativistic (bool, optional): Whether the calculation is relativistic.
                             Defaults to False.
        conv_thr (float): The convergence threshold for the electronic self-consistent field.
        electron_maxstep (int): The maximum number of electronic self-consistent field iterations.


    Returns:
        str: The &ELECTRONS section of the input file.
    """

    electrons_section = f"""&ELECTRONS
    conv_thr         = {conv_thr}
    electron_maxstep = {electron_maxstep}
"""

    if relativistic:
        electrons_section += """    mixing_beta      = 0.4
    startingpot      = 'file'
/
"""
        return electrons_section

    else:
        electrons_section += "/\n"
        return electrons_section


def generate_atomic_species_section(element_names: List[str],
                                    pseudo_list: Dict[str, str],
                                    atomic_weights: List[float]) -> str:
    """
    Generates the ATOMIC_SPECIES section of the input file.

    Args:
        element_names (list): List of element names.
        pseudo_list (dict): Dictionary of element names with their corresponding pseudopotential files.
        atomic_weights (list): List of atomic weights.

    Returns:
        str: The ATOMIC_SPECIES section of the input file.
    """

    atomic_species_section = "ATOMIC_SPECIES\n"
    for element, weight, pseudo in zip(element_names, atomic_weights, pseudo_list.values()):
        atomic_species_section += f"{element:<2}   {weight:>8.4f}    {pseudo}\n"

    return atomic_species_section


def generate_atomic_positions_section(atomic_labels: List[str], atomic_positions: List[str]) -> str:
    """
    Generates the ATOMIC_POSITIONS section of the input file.

    Args:
        atomic_labels (list): List of atomic labels.
        atomic_positions (list): List of atomic positions.

    Returns:
        str: The ATOMIC_POSITIONS section of the input file.
    """

    atomic_positions_section = "ATOMIC_POSITIONS crystal\n"
    for element, position in zip(atomic_labels, atomic_positions):
        atomic_positions_section += f"{element:<2}    {position}\n"

    return atomic_positions_section


def generate_cell_parameters_section(lattice_vectors: List[str]) -> str:
    """
    Generates the CELL_PARAMETERS section of the input file.

    Args:
        lattice_vectors (list): List of lattice vectors.

    Returns:
        str: The CELL_PARAMETERS section of the input file.
    """

    cell_parameters_section = "CELL_PARAMETERS angstrom\n"
    for vector in lattice_vectors:
        cell_parameters_section += f"    {vector}\n"

    return cell_parameters_section
