"""Module for collecting data from Quantum ESPRESSO output files.

This module provides functionality to extract and process data from Quantum ESPRESSO output files,
including band structure, Fermi energies, atomic states, and projected density of states (PDOS).
It also includes utilities for handling spin-orbit coupling (SOC) cases and generating derived data
such as projected bands and PDOS files.

Classes:
    SpinOrbitHandler: Handles SOC-related logic, including skipping SOC cases and managing errors.

Functions:
    collect_dft_data: Extracts data from Quantum ESPRESSO output files using a specified extractor function.
    collect_band_numbers: Collects band numbers from Quantum ESPRESSO output files.
    collect_fermi_energies: Collects Fermi energies from Quantum ESPRESSO output files.
    collect_number_of_atomic_states: Collects the number of atomic states from KPDOS output files.
    collect_atomic_states_info: Collects atomic states information from KPDOS or PDOS output files.
    run_awk_script: Executes an AWK script to generate projected bands data.
    run_sum_pdos: Executes the Quantum ESPRESSO sumpdos.x script to generate PDOS files.
    generate_projected_bands: Generates projected bands data if not already present.
    generate_pdos: Generates PDOS files if not already present.
    prepare_bands_info: Prepares band structure information by extracting data from output files.
    prepare_wannier_info: Prepares Wannier information by extracting data from NSCF Wannier output files.
    prepare_pdos_info: Prepares PDOS information by extracting data from output files.
    display_dft_info: Displays DFT calculation information in a formatted table.
    display_atomic_states: Displays atomic states information in a formatted table.
    display_wannier_info: Displays Wannier calculation information in a formatted table.
"""
import os.path
from sys import argv
from typing import Any

from rich import box
from rich.table import Table

from ui.ui_helpers import prompt_input, print_warning, print_header, console
from utils.file_parser import *
from core.project_setup import initialize_project
from core.input_handler import get_atomic_states
from data.models import BandInfo, WannierSetup, ProjectSetup, DOSSetup
from subprocess import CalledProcessError, run
from core.project_setup import ProjectInitializationError


class SpinOrbitHandler:
    """
    A class to handle spin-orbit coupling (SOC) related logic, including skipping SOC cases
    and managing errors during data collection from Quantum ESPRESSO output files.

    Attributes:
        skip_soc (bool): Indicates whether SOC cases should be skipped automatically.
    """

    def __init__(self, skip_soc: bool = False) -> None:
        """
        Initializes the SpinOrbitHandler with the option to skip SOC cases.

        Args:
            skip_soc (bool): Whether to skip SOC cases. Defaults to False.
        """
        self.skip_soc = skip_soc

    def should_skip(self, flag: str) -> bool:
        """
        Determines if a given case should be skipped based on the SOC flag.

        Args:
            flag (str): The flag indicating whether the case involves SOC (e.g., "_soc").

        Returns:
            bool: True if the case should be skipped, False otherwise.
        """
        return self.skip_soc and flag == "_soc"

    def handle_error(self, flag: str) -> bool:
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
            print_info("Spin-orbit was set to be skipped. Continuing...")
            return True

        skip_soc_input = prompt_input(
            'Do you want to skip spin-orbit case? Enter "y" if you want to skip spin-orbit or "n" to quit the program: '
        ).lower()

        if skip_soc_input == "n":
            exit(1)
        return True

def collect_dft_data(path: str,
                     compound_name: str,
                     flag: str,
                     extractor_func: callable,
                     *,
                     atom: str = None,
                     orbital: str = None,
                     is_pdos: bool = False) -> None | Tuple[None, bool] | Tuple[Any, bool]:
    """
    Collect data from Quantum ESPRESSO output files using a specified extractor function.

    Args:
        path (dict): The file path.
        compound_name (str): Name of the compound being analyzed.
        flag (str): Suffix for the file name (e.g., "_soc" or "").
        extractor_func (callable): Function used to extract specific data from the file.
        atom (str): Atomic symbol
        orbital (str): Orbital type (e.g., "s", "p", "d")
        is_pdos (bool): Whether the data is from a PDOS file.

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
                    data = extractor_func(path, compound_name, flag) if \
                        not is_pdos else extractor_func(path, compound_name, flag, is_pdos)
                    return data, True

            case (True, False) | (False, True):
                raise ValueError(
                    """Both atom and orbital should be either None or not None.
                    If you want to extract atomic states, please provide both atom and orbital."""
                )

            case (False, False):
                data = extractor_func(path, compound_name, flag, atom, orbital) if \
                    not is_pdos else extractor_func(path, compound_name, flag, atom, orbital, is_pdos)
                return data, True

    except (FileNotFoundError, ValueError) as e:
        print_error(f"Error: {e}")
        return None, False


def collect_band_numbers(paths: Dict[str, List[str]],
                         compound_name: str,
                         spin_orbit_flags: List[str],
                         skip_soc: bool = False) -> list[int]:
    """
    Collect band numbers from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: List of band numbers
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    number_of_bands_list = []

    for path, flag in zip(paths["pw_bands_output_paths"], spin_orbit_flags):
        if soc_handler.should_skip(flag):
            continue

        data, success = collect_dft_data(path, compound_name, flag, extract_band_number)

        if not success:
            if soc_handler.handle_error(flag):
                return number_of_bands_list
        else:
            number_of_bands_list.append(data)

    return number_of_bands_list


def collect_fermi_energies(paths: Dict[str, List[str]],
                           compound_name: str,
                           spin_orbit_flags: List[str],
                           skip_soc: bool = False,
                           is_pdos: bool = False) -> List[float]:
    """
    Collect Fermi energies from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations
        is_pdos (bool): Whether to collect Fermi energies from PDOS files

    Returns:
        list: List of Fermi energies
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    fermi_energy_list = []

    for path, flag in zip(paths["nscf_output_paths"] if is_pdos else paths["scf_output_paths"],
                          spin_orbit_flags):

        if soc_handler.should_skip(flag):
            continue

        data, success = collect_dft_data(path, compound_name, flag, extract_fermi_energy, is_pdos=is_pdos)

        if not success:
            if soc_handler.handle_error(flag):
                return fermi_energy_list
        else:
            fermi_energy_list.append(data)

    return fermi_energy_list

def collect_number_of_atomic_states(paths: Dict[str, List[str]],
                                    compound_name: str,
                                    spin_orbit_flags: List[str],
                                    skip_soc: bool = False) -> List[int]:
    """
    Collect the number of atomic states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: List of number of atomic states
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    number_of_atomic_states_list = []

    for path, flag in zip(paths["kpdos_output_paths"], spin_orbit_flags):
        if soc_handler.should_skip(flag):
            continue

        data, success = collect_dft_data(path, compound_name, flag, extract_number_of_atomic_states)

        if not success:
            if soc_handler.handle_error(flag):
                return number_of_atomic_states_list
        else:
            number_of_atomic_states_list.append(data)

    return number_of_atomic_states_list


def collect_atomic_states_info(paths: Dict[str, List[str]],
                               compound_name: str,
                               spin_orbit_flags: List[str],
                               skip_soc: bool = False,
                               is_pdos: bool = False) -> List[Dict[Any, Any]]:
    """
    Collect the atomic info states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations
        is_pdos (bool): Whether to collect atomic states info from PDOS files

    Returns:
        list: A list of dictionaries containing the indices and orbital weights of each atomic state
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    atomic_states_info_list = []

    atomic_projection_list = get_atomic_states()

    for path, flag in zip(paths["kpdos_output_paths"] if not is_pdos
                          else paths["pdos_output_paths"], spin_orbit_flags):

        atomic_states_info = {}
        if soc_handler.should_skip(flag):
            continue

        for atom, orbital in atomic_projection_list:
            data, success = collect_dft_data(path,
                                             compound_name,
                                             flag,
                                             extract_atomic_states_info,
                                             atom=atom,
                                             orbital=orbital,
                                             is_pdos=is_pdos)

            if not success:
                if soc_handler.handle_error(flag):
                    break
            else:
                atomic_states_info.update(data)

        atomic_states_info_list.append(atomic_states_info)

    return atomic_states_info_list


def run_awk_script(number_of_atomic_states: int,
                   fermi_energy: float,
                   kpdos_output_dir: str,
                   projbands_dir: str) -> None:
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
    print_info("Calculating projected bands...")

    awk_command = (
        f"awk -v firststate=1 "
        f"-v laststate={number_of_atomic_states} "
        f"-v ef={fermi_energy} "
        f"-f utils/projwfc_to_bands.awk {kpdos_output_dir} > {projbands_dir}"
    )

    run(awk_command, shell=True, check=True, capture_output=True)


def run_sum_pdos(atomic_projection: Tuple[str, str]) -> None:
    """
    Executes the Quantum ESPRESSO sumpdos.x script to get the desired PDOS files.

    """

    print_info(f"Summing the PDOS files for {atomic_projection[0]}-{atomic_projection[1]}")

    sum_pdos_command = (f"sumpdos.x "
                        f"*\({atomic_projection[0]}\)*\({atomic_projection[1]}*\) "
                        f"> pdos_{atomic_projection[0]}_{atomic_projection[1]}.dat")

    run(sum_pdos_command, shell=True, check=True, capture_output=True)


def generate_projected_bands(paths: Dict[str, List[str]],
                             number_of_atomic_states_list: List[int],
                             fermi_energies: List[float]) -> List[bool]:
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
        fermi_energies (list): A list of floats representing the Fermi energy values for each calculation output.
    Returns:
        list: A list of boolean values indicating the success (True) or failure (False)
              of the projected bands generation for each file.
    """
    print_header("Generating Projected Bands Data")

    # List to track whether the projbands generation was successful for each file
    success_list = []

    # Iterating over the KPDOS output paths and corresponding projbands paths
    for i, (projbands_dir, kpdos_output_dir,
         number_of_atomic_states, fermi_energy) in enumerate(zip(
        paths["projbands_paths"], paths["kpdos_output_paths"],
        number_of_atomic_states_list, fermi_energies
    )):
        console.rule(f"Generating file {i + 1} of {len(paths['projbands_paths'])}")

        # Checking if the projbands file already exists
        if os.path.exists(projbands_dir):
            print_warning(f"File already exists: `{os.path.basename(projbands_dir)}`\n")
            success_list.append(True)
            continue

        try:
            with console.status("Calculating projected bands..."):

                # Running the AWK script to generate the projbands file
                run_awk_script(number_of_atomic_states, fermi_energy, kpdos_output_dir, projbands_dir)

            print_success(f"Created: `{os.path.basename(projbands_dir)}`\n")
            success_list.append(True)

        except CalledProcessError as e:

            # Handling errors during the AWK script execution
            print_error(f"Failed to generate: `{os.path.basename(projbands_dir)}`")
            print_error(e.stderr.decode("utf-8"))
            success_list.append(False)

    return success_list


def generate_pdos(paths: Dict[str, List[str]],
                  atomic_projection_list: List[str]
                  ) -> List[bool]:
    """
    Generates Projected Density of States (PDOS) files if not already present.

    Args:
        paths (Dict[str, List[str]]): Dictionary containing output file paths
        atomic_projection_list (List[str]): List of atomic projections in "atom-orbital" format

    Returns:
        List[bool]: List of boolean values indicating success/failure for each file generation
    """
    print_header("Generating PDOS Data")

    # List to track whether the pdos generation was successful for each file
    success_list = []

    total_files = len(paths["pdos_output_paths"]) * len(atomic_projection_list)
    current_file = 0

    # Iterating over the PDOS output paths and corresponding PDOS data
    for pdos_dir in paths["pdos_output_paths"]:

        os.chdir(os.path.dirname(pdos_dir))
        for atomic_projection in atomic_projection_list:

            current_file += 1
            console.rule(f"Generating file {current_file} of {total_files}")

            atom, orbital = atomic_projection.split('-')

            # Checking if the PDOS file already exists
            pdos_data_file = os.path.join(os.path.dirname(pdos_dir), f"pdos_{atom}_{orbital}.dat")
            if os.path.exists(pdos_data_file):
                print_warning(f"File already exists: `{os.path.basename(pdos_data_file)}`\n")
                success_list.append(True)
                continue

            try:
                with console.status("Calculating PDOS..."):
                    # Running the sumpdos.x script to generate the PDOS files
                    run_sum_pdos((atom, orbital))

                print_success(f"Created: `{os.path.basename(pdos_data_file)}`\n")
                success_list.append(True)

            except CalledProcessError as e:
                # Handling errors
                print_error(f"Failed to generate: `{os.path.basename(pdos_data_file)}`")
                print_error(e.stderr.decode("utf-8"))
                success_list.append(False)

    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    return success_list


def prepare_bands_info(project: ProjectSetup) -> ProjectSetup:
    """
    Prepare projected bands information by extracting data from Quantum ESPRESSO output files.

    Args:
        project (ProjectSetup): Project setup object containing paths and parameters.

    Returns:
        ProjectSetup: Updated project setup object with DFT information.
    """
    print_header("Bands Info Extraction")

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

    band_info = BandInfo(
        number_of_bands=number_of_bands_list,
        fermi_energies=fermi_energies,
        number_of_atomic_states=number_of_atomic_states_list,
        atomic_states_info=atomic_states_info_list,
        spin_orbit_flags=spin_orbit_flags
    )

    # Generate projected bands
    success = generate_projected_bands(
        project.output_paths,
        band_info.number_of_atomic_states,
        band_info.fermi_energies
    )

    if not all(success):
        raise ProjectInitializationError("Some projbands files were not generated successfully.")

    # Add DFT info to project
    project.add_bands_info(band_info)
    return project


def prepare_wannier_info(project: ProjectSetup) -> ProjectSetup:
    """Prepare Wannier information by extracting data from NSCF Wannier output files.

    Args:
        project (PojectSetup): Project setup object containing paths and parameters.

    Returns:
        WannierSetup: Configuration object for Wannier calculations

    Raises:
        ProjectInitializationError: If initialization fails
    """
    print_header("Wannier Info Extraction")

    fermi_energies = []
    alat_parameters = []
    skip_normal = False

    spin_orbit_flags = ["", "_soc"]

    nscf_paths = project.output_paths["nscf_wannier_output_paths"]

    for path, flag in zip(nscf_paths, spin_orbit_flags):
        try:
            alat, fermi_energy = extract_wannier_parameters(path, project.compound_name, flag)
            alat_parameters.append(alat)
            fermi_energies.append(fermi_energy)

        except FileNotFoundError as e:
            if flag == "":

                response = prompt_input("Non-SOC calculation files missing. Skip non-SOC case? (y/n): ")
                if response.lower() == "y":
                    skip_normal = True
                    continue
            raise ProjectInitializationError("Required Wannier files missing") from e

        except ValueError as e:
            raise ProjectInitializationError(f"Failed to extract Wannier parameters: {str(e)}")

    wannier_setup = WannierSetup(
        fermi_energies=fermi_energies,
        alat_parameters=alat_parameters,
        skip_normal=skip_normal
    )

    # Add Wannier setup to project configuration
    project.add_wannier_setup(wannier_setup)
    return project


def prepare_pdos_info(project: ProjectSetup) -> ProjectSetup:
    """
    Prepare PDOS (Projected Density of States) information by extracting data from Quantum ESPRESSO output files.

    Args:
        project (ProjectSetup): Project setup object containing paths and parameters.

    Returns:
        ProjectSetup: Updated project setup object with PDOS information.
    """
    print_header("PDOS Info Extraction")

    spin_orbit_flags = ["", "_soc"]
    fermi_energies = collect_fermi_energies(project.output_paths,
                                            project.compound_name,
                                            spin_orbit_flags,
                                            project.skip_soc,
                                            is_pdos=True)

    atomic_states_info_list = collect_atomic_states_info(project.output_paths,
                                                         project.compound_name,
                                                         spin_orbit_flags,
                                                         project.skip_soc,
                                                         is_pdos=True)

    dos_setup = DOSSetup(fermi_energies=fermi_energies,
                        spin_orbit_flags=spin_orbit_flags,
                        atomic_states_info=atomic_states_info_list)

    project.add_dos_setup(dos_setup)

    success = generate_pdos(project.output_paths, list(project.dos_setup.atomic_states_info[0].keys()))
    if not all(success):
        raise ProjectInitializationError("Some PDOS files were not generated successfully.")

    return project


def display_dft_info(band: int, fermi_energy: float, states: int, stress_amount: str | None = None) -> None:
    """
    Display DFT (Density Functional Theory) calculation information in a formatted table.

    Args:
        band (int): The number of bands in the calculation.
        fermi_energy (float): The Fermi energy value in eV.
        states (int): The number of atomic states.
        stress_amount (str | None): The stress amount in the format '1_<percent>' (e.g., '1_30')
                                    or None if no stress is applied.

    Returns:
        None: This function prints the DFT calculation information to the console.
    """
    table = Table(box=box.ROUNDED, title="DFT Calculation Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    if stress_amount:
        strain_percent = float(stress_amount.replace('_', '.')) * 100
        table.caption = f"Results for {strain_percent:.2f}% strain"

    # Add rows for each property
    table.add_row("Number of bands", str(band))
    table.add_row("Fermi energy (eV)", f"{fermi_energy:.4f}")
    table.add_row("Atomic states", str(states))

    console.print(table)


def display_atomic_states(atomic_states_info: Dict[str, Any]) -> None:
    """
    Display atomic states information in a formatted table.

    Args:
        atomic_states_info (Dict[str, Any]): A dictionary containing atomic states and their properties.

    Returns:
        None: This function prints the atomic states information to the console.
    """
    table = Table(title="Atomic States Info", box=box.ROUNDED)
    table.add_column("State", style="cyan")
    table.add_column("Properties", style="green")

    for state, info in atomic_states_info.items():
        table.add_row(state, str(info))

    console.print(table)


def display_wannier_info(fermi_energy: float, alat_parameter: float) -> None:
    """
    Display Wannier calculation information in a formatted table.

    Args:
        fermi_energy (float): The Fermi energy value in eV.
        alat_parameter (float): The lattice parameter in Ångströms.

    Returns:
        None: This function prints the Wannier calculation information to the console.
    """
    table = Table(title="Wannier Info", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Fermi energy (eV)", f"{fermi_energy:.4f}")
    table.add_row("Lattice parameter (Å)", f"{alat_parameter:.6f}")

    console.print(table)

# Test to ensure the module works as expected
if __name__ == "__main__":
    """
    Main entry point for testing the module.

    This script validates that the prepare_dft_info has executed successfully and prints the extracted 
    information if successful.
    """
    os.chdir("..")

    # Create initialization options table
    options_table = Table(title="Available Initialization Types")
    options_table.add_column("Type", style="cyan")
    options_table.add_column("Description", style="green")
    options_table.add_row("wannier", "Prepare Wannier bands comparison setup")
    options_table.add_row("bands", "Extract band structure information")
    options_table.add_row("pdos", "Process projected density of states")
    console.print(options_table)

    is_input = len(argv) == 3

    response = prompt_input("Select initialization type: ").strip().lower()

    match response:
        case "wannier":
            project = initialize_project(argv, is_input, is_wannier=True)
            prepare_wannier_info(project)
            is_wannier = True
            is_pdos = False

        case "bands":
            project = initialize_project(argv, is_input)
            prepare_bands_info(project)
            is_wannier = False
            is_pdos = False

        case "pdos":
            project = initialize_project(argv, is_input, is_pdos=True)
            prepare_pdos_info(project)
            is_wannier = False
            is_pdos = True

        case _:
            raise ValueError("Invalid initialization type! Valid choices are: wannier, bands, pdos")

    print_info("Setup completed successfully.\n")

    if project.include_stress:
        print_header("Reporting Projected Bands Info")
        print('\n')
        for stress_amount, band, fermi_energy, states, atomic_states_info in zip(
                [None] + project.stress_amounts,
                project.band_info.number_of_bands,
                project.band_info.fermi_energies,
                project.band_info.number_of_atomic_states,
                project.band_info.atomic_states_info
        ):
            display_dft_info(band, fermi_energy, states, stress_amount)
    else:

        if not is_wannier and not is_pdos:
            print_header("Reporting Projected Bands Info")
            print('\n')
            for band, fermi_energy, states, atomic_states_info, flag in zip(
                    project.band_info.number_of_bands,
                    project.band_info.fermi_energies,
                    project.band_info.number_of_atomic_states,
                    project.band_info.atomic_states_info,
                    ["", "(SOC)"]
            ):
                console.rule(f"Info for {'Non-SOC' if flag == '' else 'SOC'} calculation")
                display_dft_info(band, fermi_energy, states)
                display_atomic_states(project.band_info.atomic_states_info[0])
                print('\n')

        elif is_pdos:
            print_header("Reporting PDOS Info")
            for fermi_energy, flag in zip(
                    project.dos_setup.fermi_energies,
                    ["", "(SOC)"]
            ):
                print_info(f"Fermi energy {flag}: {fermi_energy:.4f} eV")
        else:
            print_header("Reporting Wannier Info")
            print('\n')
            for fermi_energy, alat_parameter, flag in zip(
                    project.wannier_setup.fermi_energies,
                    project.wannier_setup.alat_parameters,
                    ["(SOC)"] if project.wannier_setup.skip_normal else ["", "(SOC)"]
            ):
                console.rule(f"Info for {'Non-SOC' if flag == '' else 'SOC'} calculation")
                display_wannier_info(fermi_energy, alat_parameter)