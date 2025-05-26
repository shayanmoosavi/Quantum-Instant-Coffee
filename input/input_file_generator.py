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
import argparse
from sys import argv
from typing import Tuple

from data.fetch_atomic_info import get_atomic_weights
from input.generators.kpoints import generate_k_points_section
from input.generators.sections import *
from ui.ui_helpers import prompt_input, print_error, print_info, print_success, console, progress_track, print_header
from utils.file_parser import get_poscar_data
from ui.print_thanks import print_animated_ascii
from core.project_setup import initialize_project
from core.input_handler import get_pseudopotential_files
from data.models import ProjectSetup


def generate_pw_input_file(calculation_type: str,
                           project: ProjectSetup,
                           atomic_weights: List[float],
                           pseudo_list: List[str],
                           atomic_positions: List[str],
                           lattice_vectors: List[str],
                           relativistic: bool = False,
                           rel_pseudo_list: bool = None,
                           kmesh: Tuple[int, int, int] = None,
                           nbnds: int = None) -> str | None:
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
        kmesh (tuple, optional): K-point mesh density. Defaults to None.
        nbnds (int, optional): Number of bands. Defaults to None.

    Returns:
        str: The complete input file for Quantum ESPRESSO.

    Raises:
        InputGenerationError: If the calculation type is invalid.
    """
    valid_calc_types = ("relax", "vc-relax", "scf", "bands", "nscf")

    if calculation_type not in valid_calc_types:
        raise InputGenerationError(f"Invalid calculation type: {calculation_type}. "
                                   f"Valid types are: {', '.join(valid_calc_types)}")

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
                if nbnds is None:
                    number_of_bands = int(
                        prompt_input(
                            f"Enter the number of bands for {calculation_type + ('_soc' if relativistic else '')}: ")
                    )
                    if number_of_bands <= 0:
                        raise ValueError("Number of bands must be a positive integer.")
                    input_file_content += generate_system_section(project.compound_data.number_of_atoms,
                                                                  project.compound_data.atom_types,
                                                                  number_of_bands=number_of_bands,
                                                                  relativistic=relativistic)
                    break
                else:
                    input_file_content += generate_system_section(project.compound_data.number_of_atoms,
                                                                  project.compound_data.atom_types,
                                                                  number_of_bands=nbnds,
                                                                  relativistic=relativistic)
                    break
            except ValueError as e:
                print_error("Error in generating SYSTEM section:")
                print_error(str(e))
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
                if kmesh is None:
                    k_mesh_density = tuple(
                        map(
                            int,
                            prompt_input(
                                f"Enter K-point mesh density (e.g., '12 12 1') for {calculation_type + ('_soc' if relativistic else '')}: "
                            ).split(),
                        )
                    )

                    input_file_content += generate_k_points_section(calculation_type, k_mesh_density)
                else:
                    input_file_content += generate_k_points_section(calculation_type, kmesh, is_wannier=True)
            else:
                input_file_content += generate_k_points_section(calculation_type)

            return input_file_content
        except ValueError as e:
            print_error("Error in generating K_POINTS section:")
            print_error(str(e))
            continue
        except InputGenerationError as e:
            print_error("Fatal error in generating K_POINTS section:")
            print_error(str(e))
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

    input_file_content += """
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
                                dis_num_iter: int = 2500,
                                stored_nbands: int = None,
                                stored_kmesh: tuple[int, int, int] = None
                                ) -> str:
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
        stored_nbands: Number of bands from nscf_wannier calculation.
        stored_kmesh: K-point mesh density from nscf_wannier calculation.
    Returns:
        str: The formatted Wannier90 input file content.

    Raises:
        InputGenerationError: If the number of bands or k-point mesh density is not provided.
    """
    if stored_nbands is None:
        raise InputGenerationError("Number of bands must be provided from nscf_wannier calculation")

    if stored_kmesh is None:
        raise InputGenerationError("K-point mesh density must be provided from nscf_wannier calculation")

    input_file_content = f"""num_bands = {stored_nbands} ! number of bands
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

    input_file_content += f"""end atoms_frac
    
mp_grid = {stored_kmesh[0]} {stored_kmesh[1]} {stored_kmesh[2]}

begin kpoints
"""
    input_file_content += generate_k_points_section("wannier", stored_kmesh, is_wannier=True)
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
    wannier_params = WannierParams()

    print_info("Fetching atomic weights and POSCAR data...")

    with console.status("Retrieving atomic weights and POSCAR data"):

        atomic_weights = get_atomic_weights(project.compound_data.element_names)
        lattice_vectors, atomic_positions = get_poscar_data(project.poscar_file)

    print_info("Fetching the Pseudopotentials...")
    pseudo_list, rel_pseudo_list = get_pseudopotential_files(project.compound_data.element_names,
                                                             project.pseudo_dir, relativistic=True,
                                                             rel_pseudo_path=project.rel_pseudo_dir
                                                             )
    print_info("Pseudopotentials fetched successfully.")
    print_info("Starting input file generation...\n")
    print_header("Input File Generation")

    def generate_nscf_wannier(rel: bool) -> str | None:
        """Generate nscf_wannier input with parameter storage."""
        while True:
            try:
                nbands = int(prompt_input(f"Enter the number of bands for wannier{'_soc' if rel else ''}: "))
                if nbands <= 0:
                    raise ValueError("Number of bands must be a positive integer.")

                k_mesh = tuple(map(int, prompt_input(
                    f"Enter K-point mesh density (e.g., '12 12 1') for wannier{'_soc' if rel else ''}: "
                ).split()))

                # Store parameters for later use
                wannier_params.set_params(nbands, k_mesh, rel)

                return generate_pw_input_file("nscf",
                                              project,
                                              atomic_weights,
                                              pseudo_list,
                                              atomic_positions,
                                              lattice_vectors,
                                              relativistic=rel,
                                              rel_pseudo_list=rel_pseudo_list if rel else None,
                                              kmesh=k_mesh,
                                              nbnds=nbands)
            except ValueError as e:
                print_error(f"Error in input: {str(e)}")
                continue

    def generate_wannier(rel: bool) -> str:
        """Generate wannier input using stored parameters."""
        nbands, k_mesh = wannier_params.get_params(rel)
        if nbands is None or k_mesh is None:
            raise InputGenerationError("Wannier parameters not set. Generate nscf_wannier first.")

        return generate_wannier_input_file(
            project.compound_data.element_names,
            atomic_positions,
            lattice_vectors,
            project.compound_data.atomic_labels,
            relativistic=rel,
            stored_nbands=nbands,
            stored_kmesh=k_mesh
        )

    # Map input patterns to their generator functions
    generator_map = {
        "relax_input": lambda rel: generate_pw_input_file("relax", project, atomic_weights,
                                                          pseudo_list, atomic_positions, lattice_vectors,
                                                          relativistic=rel,
                                                          rel_pseudo_list=rel_pseudo_list if rel else None),
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
        "nscf_wannier_input": generate_nscf_wannier,
        "pw2wan_input": lambda rel: generate_pw2wannier_input_file(compound_name, relativistic=rel),
        "wannier_input": generate_wannier
    }

    generated_files = []

    print_info("Generating input files...")
    for key, paths in project.input_paths.items():
        input_type = key.replace("_paths", "")
        if input_type in generator_map.keys():

            # Generate the input files using the appropriate generator function
            if not project.include_stress:
                for path, relativistic in zip(paths, [False, True]):
                    file_name = os.path.basename(path)

                    if "_soc" in file_name and skip_soc:
                        print_info(f"Skipping SOC file generation for {file_name}")
                        continue

                    input_src = generator_map[input_type](relativistic)
                    generated_files.append((file_name, path, input_src))
            else:
                for path in paths:
                    file_name = os.path.basename(path)
                    input_src = generator_map[input_type](False)
                    generated_files.append((file_name, path, input_src))

    print_success("\nInput files have been generated successfully.\n")
    print_header("Writing Input Files")
    for file_name, path, content in progress_track(generated_files, description="Writing input files"):
        with open(path, "w") as f:
            f.write(content)
        print_success(f"Wrote {file_name} at:\n    {path}")

    print_success("All input files have been written successfully.")

    print_animated_ascii("ascii-art.txt")
    console.print("\nThanks for using Quantum Instant Coffee :)", style="bold cyan")

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
    # Create the parser
    parser = argparse.ArgumentParser(description="Writes input files for Quantum ESPRESSO and Wannier90 calculations.")

    # Add arguments
    parser.add_argument(
        "compound_name",
        type=str,
        help="Name of the compound (e.g., 'GaAs', 'SiO2')."
    )
    parser.add_argument(
        "poscar_file",
        type=str,
        help="Path to the POSCAR file."
    )

    # Parse the arguments
    args = parser.parse_args(argv[1:])
    compound_name, poscar_file = args.compound_name, args.poscar_file

    os.chdir("..")

    project = initialize_project(compound_name, poscar_file=poscar_file, is_input=True)
    pseudo_list, rel_pseudo_list = get_pseudopotential_files(project.compound_data.element_names,
                                                             project.pseudo_dir,
                                                             relativistic=True,
                                                             rel_pseudo_path=project.rel_pseudo_dir
                                                             )

    atomic_weights = get_atomic_weights(project.compound_data.element_names)
    lattice_vectors, atomic_positions = get_poscar_data(project.poscar_file)

    nscf_input = generate_pw_input_file(
        calculation_type="nscf",
        project=project,
        atomic_weights=atomic_weights,
        pseudo_list=pseudo_list,
        atomic_positions=atomic_positions,
        lattice_vectors=lattice_vectors,
        relativistic=True,
        rel_pseudo_list=rel_pseudo_list
    )

    print_info(nscf_input)
