"""Module to generate input files for Quantum ESPRESSO calculations.

This module provides functions to generate various sections of input files
required for Quantum ESPRESSO calculations. It includes functionality for
creating sections such as CONTROL, SYSTEM, ELECTRONS, ATOMIC_SPECIES,
ATOMIC_POSITIONS, CELL_PARAMETERS, and K_POINTS. Additionally, it provides
utilities for retrieving atomic weights from a database and generating the
complete input file.

The module is designed to handle both relativistic and non-relativistic
calculations and supports flexible configuration of input parameters.
"""

import os
from sys import argv
import sqlite3
from subprocess import run, CalledProcessError
from utils.file_parser import get_poscar_data
from init_project import initialize_project
from core.input_handler import get_pseudopotential_files
from typing import List, Dict, Tuple

from data.models import ProjectSetup


class InputGenerationError(Exception):
    """Custom exception for input file generation errors."""
    pass


def get_atomic_weights(element_names: List[str]) -> List[float] | None:
    """
    Retrieves the atomic weights for the given element names.

    Args:
        element_names (list): List of element names.

    Returns:
        list: List of atomic weights corresponding to the element names.
    """
    if not element_names:
        raise ValueError("Element names list cannot be empty.")
    try:
        conn = sqlite3.connect("../data/elements.db")
        cursor = conn.cursor()
        atomic_weights = []

        for element in element_names:
            cursor.execute("""
            SELECT atomic_weight FROM elements WHERE symbol=?;""", (element,))
            result = cursor.fetchone()
            atomic_weights.append(result[0] if result else None)

        return atomic_weights
    except sqlite3.Error as e:
        raise InputGenerationError(f"Database error: {str(e)}")

    finally:
        if conn:
            conn.close()

def generate_control_section(
        calculation_type: str,
        pseudo_dir: str,
        project_dir: str,
        compound_name: str,
        *,
        etot_conv_thr: float = 1e-8,
        forc_conv_thr:float = 1e-6,
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


def generate_k_points_section(calculation_type: str, k_mesh_density: Tuple[int] = None) -> str | None:
    """
    Generates the K_POINTS section of the input files for Quantum ESPRESSO or
    kpoints section of Wannier90 input file.

    Args:
        calculation_type (str): The calculation type (e.g., 'scf', 'bands').
        k_mesh_density (tuple): The K-point mesh density.

    Returns
        str: The K_POINTS section of the input file.
    """
    valid_calc_types = ("relax", "vc-relax", "scf", "bands", "nscf", "wannier")

    if calculation_type not in valid_calc_types:
        raise InputGenerationError(f"Invalid calculation type: {calculation_type}. "
                         f"Valid types are: {', '.join(valid_calc_types)}")

    try:
        if len(k_mesh_density) != 3:
            raise ValueError("k_mesh_density must be three integers separated by spaces.")

    except TypeError:
        if calculation_type != "bands":
            raise InputGenerationError(f"K-point mesh density cannot be None for {calculation_type} calculation.")

    if calculation_type in ["relax", "vc-relax", "scf"]:
        k_points_section = "K_POINTS automatic\n"
        k_points_section += f" {k_mesh_density[0]} {k_mesh_density[1]} {k_mesh_density[2]} 0 0 0\n"

        return k_points_section

    elif calculation_type == "nscf":
        is_wannier = input("Is this a wannier calculation? (y/n): ").strip().lower()

        if is_wannier not in ["y", "n"]:
            raise ValueError("Invalid input. Please enter 'y' for yes or 'n' for no.")

        if is_wannier == "n":
            k_points_section = "K_POINTS automatic\n"
            k_points_section += f" {k_mesh_density[0]} {k_mesh_density[1]} {k_mesh_density[2]} 0 0 0\n"

            return k_points_section

        else:
            try:
                k_points_section = run(f"../utils/kmesh.pl {k_mesh_density[0]} {k_mesh_density[1]} {k_mesh_density[2]}",
                                       shell=True, check=True, capture_output=True).stdout.decode("utf-8")
                return k_points_section
            except CalledProcessError as e:
                raise InputGenerationError(f"An error occurred in running kmesh.pl script:\n {e.stderr.decode('utf-8')}")

    elif calculation_type == "wannier":

        try:
            k_points_section = run(f"../utils/kmesh.pl {k_mesh_density[0]} {k_mesh_density[1]} {k_mesh_density[2]} wann",
                                   shell=True, check=True, capture_output=True).stdout.decode("utf-8")
            return k_points_section
        except CalledProcessError as e:
            raise InputGenerationError(f"An error occurred in running kmesh.pl script:\n {e.stderr.decode('utf-8')}")

    elif calculation_type == "bands":
        k_points_section = """K_POINTS crystal_b
4
0.0000000000    0.0000000000    0.0000000000    120 ! Gamma
0.5000000000    0.0000000000    0.0000000000    120 ! M
0.3333333333    0.3333333333    0.0000000000    120 ! K
0.0000000000    0.0000000000    0.0000000000      0 ! Gamma
"""
        return k_points_section

def generate_pw_input_file(calculation_type: str,
                           project: ProjectSetup,
                           atomic_weights: List[float],
                           pseudo_list: List[str],
                           atomic_positions: List[str],
                           lattice_vectors: List[str],
                           relativistic: bool = False,
                           rel_pseudo_list: bool = None):
    """
    Generates the complete pw.x input file for Quantum ESPRESSO.

    Args:
        calculation_type (str): The type of calculation (e.g., 'vc-relax', 'scf').
        project (ProjectSetup): Project setup object containing project information.
        atomic_weights (list): List of atomic weights.
        pseudo_list (list): List of pseudopotential files.
        atomic_positions (list): List of atomic positions.
        lattice_vectors (list): List of lattice vectors.
        relativistic (bool, optional): Whether the calculation is relativistic. Defaults to False.
        rel_pseudo_list (bool, optional): List of relativistic pseudopotential files

    Returns:
        str: The complete input file for Quantum ESPRESSO.
    """
    input_file_content = generate_control_section(calculation_type,
                                                  project.pseudo_dir
                                                  if not relativistic
                                                  else project.rel_pseudo_dir,
                                                  project.project_dir,
                                                  project.compound_name,
                                                  relativistic=relativistic)
    if calculation_type in ["nscf", "bands"]:
        while True:
            try:
                number_of_bands = int(
                    input(f"Enter the number of bands for {calculation_type + ('_soc' if relativistic else '')}: ")
                )
                if number_of_bands <= 0:
                    raise ValueError("Number of bands must be a positive integer.")
                input_file_content += generate_system_section(project.compound_data.number_of_atoms, project.compound_data.atom_types,
                                                          number_of_bands=number_of_bands, relativistic=relativistic)
                break
            except ValueError as e:
                print("Error in generating SYSTEM section:", str(e))
                continue
    else:
        input_file_content += generate_system_section(project.compound_data.number_of_atoms,
                                                      project.compound_data.atom_types, relativistic=relativistic)

    input_file_content += generate_electrons_section(relativistic=relativistic)
    if calculation_type in ["relax", "vc-relax"]:
        input_file_content += """&IONS
/
&CELL
    cell_dofree      = 'ibrav'
/
"""
    input_file_content += generate_atomic_species_section(project.compound_data.element_names,
                                                          rel_pseudo_list if relativistic else pseudo_list,
                                                          atomic_weights)
    input_file_content += generate_atomic_positions_section(project.compound_data.atomic_labels, atomic_positions)
    input_file_content += generate_cell_parameters_section(lattice_vectors)

    while True:
        try:
            if calculation_type != "bands":
                k_mesh_density = tuple(
                            map(
                                int,
                                input(
                                    f"Enter K-point mesh density (e.g., '12 12 1') for {calculation_type + ('_soc' if relativistic else '')}: "
                                ).split(),
                            )
                        )

                input_file_content += generate_k_points_section(calculation_type, k_mesh_density)
            else:
                input_file_content += generate_k_points_section(calculation_type)

            return input_file_content
        except ValueError as e:
            print("Error in generating K_POINTS section:", str(e))
            continue
        except InputGenerationError as e:
            print("Fatal error in generating K_POINTS section:", str(e))
            exit(1)


def generate_pdos_input_file(compound_name: str, *, delta: float = 0.01) -> str:
    """
    Generates the input file for projected density of states (PDOS) calculations.

    Args:
        compound_name (str): The name of the compound.
        delta (float, optional): The energy resolution for the PDOS calculation. Defaults to 0.01.

    Returns:
        str: The formatted PDOS input file content.
    """
    return f"""&PROJWFC
    outdir          = './out'
    prefix          = '{compound_name}'
    filpdos         = '{compound_name}'
    DeltaE          = {delta}
 /"""


def generate_kpdos_input_file(compound_name: str, *, delta: float = 0.01) -> str:
    """
    Generates the input file for k-resolved projected density of states (k-PDOS) calculations.

    Args:
        compound_name (str): The name of the compound.
        delta (float, optional): The energy resolution for the k-PDOS calculation. Defaults to 0.01.

    Returns:
        str: The formatted k-PDOS input file content.
    """
    return f"""&PROJWFC
    outdir       = './out'
    prefix       = '{compound_name}'
    DeltaE       = {delta}
    kresolveddos = .true.
    filpdos      = '{compound_name}.k'
    lsym         = .false.
    filproj      = '{compound_name}.proj.dat'
/"""


def generate_bands_input_file(compound_name: str) -> str:
    """
    Generates the input file for band structure calculations.

    Args:
        compound_name (str): The name of the compound.

    Returns:
        str: The formatted band structure input file content.
    """
    return f"""&BANDS
    outdir       = './out'
    prefix       = '{compound_name}'
    filband      = '{compound_name}.bands'
    lsym         = .true.
    filband      = '{compound_name}.bands'
/"""


def generate_pw2wannier_input_file(compound_name: str, relativistic: bool = False) -> str:
    """
    Generates the complete pw2wannier90.x input file for Quantum ESPRESSO.

    Args:
        compound_name (str): The name of the compound.
        relativistic (bool, optional): Whether the calculation is relativistic. Defaults to False.

    Returns:
        str: The formatted pw2wannier90.x input file content.
    """

    input_file_content = f"""&inputpp
  outdir     =  './out'   ! quantum espresso outdir
  prefix     =  '{compound_name}' ! prefix of the pw.x scf calculation
  """
    if relativistic:
        input_file_content += f"  seedname   =  '{compound_name}_wannier_soc' ! must be same as the file name of win file"
    else:
        input_file_content += f"  seedname   =  '{compound_name}_wannier' ! must be same as the file name of win file"

    input_file_content +="""
  write_amn  =  .true.
  write_mmn  =  .true.
/
"""
    return input_file_content

def generate_wannier_input_file(element_names: List[str],
                                atomic_positions: List[str],
                                lattice_vectors: List[str],
                                atomic_labels: List[str],
                                relativistic: bool = False,
                                *,
                                num_iter: int = 250,
                                dis_num_iter: int = 2500) -> str:
    """
    Generates the input file for Wannier90.

    Args:
        element_names (list): List of element names.
        atomic_positions (list): List of atomic positions.
        lattice_vectors (list): List of lattice vectors.
        atomic_labels (list): List of atomic labels.
        relativistic (bool, optional): Whether the calculation is relativistic. Defaults to False.
        num_iter (int, optional): Number of minimization iterations. Defaults to 250.
        dis_num_iter (int, optional): Number of disentanglement iterations. Defaults to 2500.

    Returns:
        str: The formatted Wannier90 input file content.
    """
    while True:
        try:
            number_of_bands = int(
                input(f"Enter the number of bands for wannier{'_soc' if relativistic else ''}: ")
            )
            if number_of_bands <= 0:
                raise ValueError("Number of bands must be a positive integer.")

            input_file_content = f"""num_bands = {number_of_bands} ! number of bands
num_wann  = 0 ! Enter the number of wannier projections here
num_iter  = {num_iter} ! number of minimization iterations

! disentaglement
! Enter the appropriate energy windows here
dis_win_min  = 0 ! lower bound of bands to extract
dis_win_max  = 0 ! upper bound of bands to extract
!dis_froz_min = 0 ! lower bound of inner window
!dis_froz_max = 0 ! upper bound of innesr window
dis_num_iter = {dis_num_iter} ! number of disentanglement iterations

! Writing the tight-binding Hamiltonian
write_hr = true

! plotting the interpolated band structure
bands_plot = true
begin kpoint_path
G 0.0000000000  0.0000000000  0.0000000000  M 0.5000000000  0.0000000000  0.0000000000
M 0.5000000000  0.0000000000  0.0000000000  K 0.3333333333  0.3333333333  0.0000000000
K 0.3333333333  0.3333333333  0.0000000000  G 0.0000000000  0.0000000000  0.0000000000
end kpoint_path

begin projections  ! Enter the atomic projections here
"""

            break
        except ValueError as e:
            print("Error in generating Wannier90 input file:", str(e))
            continue

    for element in element_names:
        input_file_content += f"{element:<2}: proj\n"

    input_file_content += "end projections\n"

    if relativistic:
        input_file_content += f"""! Required for spin orbit
spinors = true

begin unit_cell_cart
angstrom
"""
    else:
        input_file_content += """
begin unit_cell_cart
angstrom
"""
    for vector in lattice_vectors:
        input_file_content += f"    {vector}\n"

    input_file_content += """end unit_cell_cart

begin atoms_frac
"""
    for label, position in zip(atomic_labels, atomic_positions):
        input_file_content += f"{label:<2}    {position}\n"

    while True:
        try:
            k_mesh_density = tuple(
                map(
                    int,
                    input(
                        f"Enter K-point mesh density (e.g., '12 12 1') for wannier{'_soc' if relativistic else ''}: "
                    ).split(),
                )
            )
            break
        except ValueError as e:
            print("Error in generating kpoints section:", str(e))
            continue

    input_file_content += f"""end atoms_frac
    
mp_grid = {k_mesh_density[0]} {k_mesh_density[1]} {k_mesh_density[2]}

begin kpoints
"""
    input_file_content += generate_k_points_section("wannier", k_mesh_density)
    input_file_content += "end kpoints\n"

    return input_file_content



def write_input_files(project: ProjectSetup, skip_soc: bool = False) -> None:
    """
    Write generated input file templates to their respective directories.

    Args:
        project (ProjectSetup): ProjectSetup object containing project information
        skip_soc (bool): Whether to write SOC files or not
    """

    compound_name = project.compound_name

    pseudo_list, rel_pseudo_list = get_pseudopotential_files(project.compound_data.element_names,
                                                             project.pseudo_dir, relativistic=True,
                                                             rel_pseudo_path=project.rel_pseudo_dir
                                                             )

    atomic_weights = get_atomic_weights(project.compound_data.element_names)
    lattice_vectors, atomic_positions = get_poscar_data(project.poscar_file)

    # Map input patterns to their generator functions
    generator_map = {
        "relax_input": lambda rel: generate_pw_input_file("relax", project, atomic_weights,
                                                            pseudo_list, atomic_positions, lattice_vectors,
                                                          relativistic=rel, rel_pseudo_list=rel_pseudo_list if rel else None),
        "vc_relax_input": lambda rel: generate_pw_input_file("vc-relax", project, atomic_weights,
                                                             pseudo_list, atomic_positions, lattice_vectors,
                                                             relativistic=rel,
                                                             rel_pseudo_list=rel_pseudo_list if rel else None),
        "scf_input": lambda rel: generate_pw_input_file("scf", project, atomic_weights,
                                                        pseudo_list, atomic_positions, lattice_vectors,
                                                        relativistic=rel,
                                                        rel_pseudo_list=rel_pseudo_list if rel else None),
        "nscf_input": lambda rel: generate_pw_input_file("nscf", project, atomic_weights,
                                                         pseudo_list, atomic_positions, lattice_vectors,
                                                         relativistic=rel,
                                                         rel_pseudo_list=rel_pseudo_list if rel else None),
        "pw_bands_input": lambda rel: generate_pw_input_file("bands", project, atomic_weights,
                                                             pseudo_list, atomic_positions, lattice_vectors,
                                                             relativistic=rel,
                                                             rel_pseudo_list=rel_pseudo_list if rel else None),
        "pdos_input": lambda _: generate_pdos_input_file(compound_name),
        "kpdos_input": lambda _: generate_kpdos_input_file(compound_name),
        "bands_input": lambda _: generate_bands_input_file(compound_name),
        "nscf_wannier_input": lambda rel: generate_pw_input_file("nscf", project, atomic_weights,
                                                                 pseudo_list, atomic_positions, lattice_vectors,
                                                                 relativistic=rel,
                                                                 rel_pseudo_list=rel_pseudo_list if rel else None),
        "pw2wan_input": lambda rel: generate_pw2wannier_input_file(compound_name, relativistic=rel),
        "wannier_input": lambda rel: generate_wannier_input_file(project.compound_data.element_names,
                                                                    atomic_positions, lattice_vectors,
                                                                    project.compound_data.atomic_labels,
                                                                    relativistic=rel)
    }

    for key, paths in project.input_paths.items():
        input_type = key.replace("_paths", "")
        if input_type in generator_map.keys():

            # Generate the input files using the appropriate generator function
            if not project.include_stress:
                for path, relativistic in zip(paths, [False, True]):
                    file_name = path.split("/")[-1]
                    if "_soc" in file_name and skip_soc:
                        print(f"Skipping SOC file generation for {file_name}", flush=True)
                        continue
                    if input_type == "nscf_wannier_input":
                        print("\n(This is for wannier90 calculation)")
                    input_src = generator_map[input_type](relativistic)
                    with open(path, "w") as file:
                        file.write(input_src)
                    print(f"Wrote {file_name} at:\n    {path}", flush=True)
            else:
                for path in paths:
                    file_name = path.split("/")[-1]
                    input_src = generator_map[input_type](False)
                    with open(path, "w") as file:
                        file.write(input_src)
                    print(f"Wrote {file_name} at:\n    {path}", flush=True)

    print("\nInput files have been generated successfully.")


if __name__ == "__main__":
    """
    Main entry point for the script.

    This block initializes the project, retrieves necessary data, and generates
    the NSCF input file for Quantum ESPRESSO calculations. It performs the following steps:
    1. Determines if the script is called for input file generation.
    2. Initializes the project setup using command-line arguments.
    3. Retrieves pseudopotential files for the specified elements.
    4. Fetches atomic weights and POSCAR data (lattice vectors and atomic positions).
    5. Generates the NSCF input file using the provided data and configuration.
    6. Prints the generated NSCF input file content.
    """

    is_input = len(argv) == 3
    project = initialize_project(argv, is_input)

    pseudo_list, rel_pseudo_list = get_pseudopotential_files(project.compound_data.element_names,
                                            project.pseudo_dir, relativistic=True, rel_pseudo_path=project.rel_pseudo_dir
                                            )

    atomic_weights = get_atomic_weights(project.compound_data.element_names)
    lattice_vectors, atomic_positions = get_poscar_data(project.poscar_file)

    nscf_input = generate_pw_input_file(
        calculation_type="nscf",
        project = project,
        atomic_weights=atomic_weights,
        pseudo_list=pseudo_list,
        atomic_positions=atomic_positions,
        lattice_vectors=lattice_vectors,
        relativistic=True,
        rel_pseudo_list=rel_pseudo_list
    )

    print(nscf_input)
