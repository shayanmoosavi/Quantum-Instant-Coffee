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
"""
import argparse
import os.path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from sys import argv
from typing import Any, Callable, Optional

from ui.display_data import display_dft_info, display_atomic_states, display_wannier_info
from ui.ui_helpers import prompt_input, print_warning, print_header, console
from utils.external_tools import run_awk_script, run_sum_pdos
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
        skip_normal (bool): Indicates whether non-SOC cases should be skipped automatically.
        soc_found (bool): Tracks whether SOC files have been successfully found.
        normal_found (bool): Tracks whether non-SOC files have been successfully found.
    """

    def __init__(self, skip_soc: bool = False, skip_normal: bool = False) -> None:
        """
        Initializes the SpinOrbitHandler with options to skip SOC or non-SOC cases.

        Args:
            skip_soc (bool): Whether to skip SOC cases. Defaults to False.
            skip_normal (bool): Whether to skip non-SOC cases. Defaults to False.
        """
        self.skip_soc = skip_soc
        self.skip_normal = skip_normal
        self.soc_found = False
        self.normal_found = False

    def should_skip(self, flag: str) -> bool:
        """
        Determines if a given case should be skipped based on the SOC flag.

        Args:
            flag (str): The flag indicating whether the case involves SOC (e.g., "_soc").

        Returns:
            bool: True if the case should be skipped, False otherwise.
        """
        if flag == "_soc":
            return self.skip_soc
        else:
            return self.skip_normal

    def mark_found(self, flag: str) -> None:
        """
        Mark that files for a specific case (SOC or non-SOC) have been found.

        Args:
            flag (str): The flag indicating whether the case involves SOC (e.g., "_soc" or "").
        """
        if flag == "_soc":
            self.soc_found = True
        else:
            self.normal_found = True

    def handle_error(self, flag: str) -> bool:
        """
        Handles errors encountered during data collection. Provides the user with the option
        to skip the case or exit the program based on what files are available.

        Args:
            flag (str): The flag indicating whether the case involves SOC (e.g., "_soc" or "").

        Returns:
            bool: True if the case should be skipped, False otherwise.

        Raises:
            SystemExit: If the user chooses not to skip the case and no other cases are available,
                       or if neither SOC nor non-SOC files are found.
        """
        # Determine case type for user-friendly messaging
        case_type = "spin-orbit (SOC)" if flag == "_soc" else "non-SOC"
        opposite_case = "non-SOC" if flag == "_soc" else "spin-orbit (SOC)"

        # Check if this case was already set to be skipped
        if (flag == "_soc" and self.skip_soc) or (flag == "" and self.skip_normal):
            print_info(f"{case_type.capitalize()} was set to be skipped. Continuing...")
            return True

        # If neither case has been found yet, prompt the user to skip or exit
        if not self.soc_found and not self.normal_found:

            skip_input = prompt_input(
                f'{case_type} file not found. Do you want to skip {case_type} case? Enter "y" to skip {case_type} '
                f'or "n" to quit the program: '
            ).lower()

            if skip_input == "y":
                # Set the appropriate skip flag for future reference
                if flag == "_soc":
                    self.skip_soc = True
                else:
                    self.skip_normal = True
                return True
            else:
                exit(1)

        # If we have found files for the opposite case, allow skipping this one
        elif (flag == "_soc" and self.normal_found) or (flag == "" and self.soc_found):
            skip_input = prompt_input(
                f'{case_type.capitalize()} files not found, but {opposite_case} files are available. '
                f'Do you want to skip {case_type} case? Enter "y" to skip {case_type} '
                f'or "n" to quit the program: '
            ).lower()

            if skip_input == "y":
                # Set the appropriate skip flag for future reference
                if flag == "_soc":
                    self.skip_soc = True
                else:
                    self.skip_normal = True
                return True
            else:
                exit(1)

        # If no files have been found for either case, exit
        else:
            print_error("No valid files found for either SOC or non-SOC calculations.")
            exit(1)

    def validate_at_least_one_case(self) -> None:
        """
        Validates that at least one case (SOC or non-SOC) has been successfully processed.

        Raises:
            SystemExit: If neither SOC nor non-SOC files were found and processed.
        """
        if not self.soc_found and not self.normal_found:
            print_error("No valid files found for either SOC or non-SOC calculations.")
            print_error("Cannot proceed without at least one valid calculation type.")
            exit(1)


def collect_dft_data(path: str,
                     compound_name: str,
                     flag: str,
                     extractor_func: Callable,
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
        extractor_func (Callable): Function used to extract specific data from the file.
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

    return None, False


@dataclass
class CollectionConfig:
    """Configuration for data collection operations."""
    paths: Dict[str, List[str]]
    compound_name: str
    spin_orbit_flags: List[str]
    skip_soc: bool = False
    skip_normal: bool = False
    is_pdos: bool = False


class DataExtractor(ABC):
    """Abstract base class for data extraction strategies."""

    @abstractmethod
    def extract_data(self, path: str, compound_name: str, flag: str, **kwargs) -> Tuple[Any, bool]:
        """Extract data from a file."""
        pass

    @abstractmethod
    def get_path_key(self) -> str:
        """Return the key for accessing paths in the paths dictionary."""
        pass

    @abstractmethod
    def get_success_message(self, **kwargs) -> str:
        """Return success message for logging."""
        pass


class SimpleDataExtractor(DataExtractor):
    """Extractor for single value extraction."""

    def __init__(self, extractor_func: Callable, path_key: str, data_name: str):
        self.extractor_func = extractor_func
        self.path_key = path_key
        self.data_name = data_name

    def extract_data(self, path: str, compound_name: str, flag: str, **kwargs) -> Tuple[Any, bool]:
        is_pdos = kwargs.get('is_pdos', False)
        return collect_dft_data(path, compound_name, flag, self.extractor_func, is_pdos=is_pdos)

    def get_path_key(self) -> str:
        return self.path_key

    def get_success_message(self, **kwargs) -> str:
        return f"Successfully extracted {self.data_name}.\n"


class AtomicStatesExtractor(DataExtractor):
    """Extractor for atomic states information."""

    def __init__(self, path_key: str):
        self.path_key = path_key
        self.atomic_projection_list = get_atomic_states()

    def extract_data(self, path: str, compound_name: str, flag: str, **kwargs) -> Tuple[Any, bool]:
        atomic_states_info = {}
        is_pdos = kwargs.get('is_pdos', False)

        for atom, orbital in self.atomic_projection_list:
            data, success = collect_dft_data(
                path, compound_name, flag, extract_atomic_states_info,
                atom=atom, orbital=orbital, is_pdos=is_pdos
            )

            if not success:
                return None, False

            atomic_states_info.update(data)

        return atomic_states_info, True

    def get_path_key(self) -> str:
        return self.path_key

    def get_success_message(self, **kwargs) -> str:
        return "\nSuccessfully extracted atomic states information.\n"


class DataCollector:
    """Template method class for collecting data from Quantum ESPRESSO files."""

    def __init__(self, extractor: DataExtractor):
        self.extractor = extractor

    def collect(self, config: CollectionConfig) -> List[Any]:
        """
        Template method for data collection.

        Args:
            config: Collection configuration

        Returns:
            List of collected data
        """
        soc_handler = SpinOrbitHandler(config.skip_soc, config.skip_normal)
        results = []

        # Get the appropriate paths based on the extractor
        paths = self._get_paths(config)

        for path, flag in zip(paths, config.spin_orbit_flags):
            if isinstance(self.extractor, AtomicStatesExtractor):
                console.rule(f"Getting atomic projections info {'(SOC)' if flag else '(Non-SOC)'}")
            if soc_handler.should_skip(flag):
                continue

            result = self._process_single_case(path, config, flag, soc_handler)
            if result is not None:
                results.append(result)

        # Validate that at least one case was successful
        soc_handler.validate_at_least_one_case()
        return results

    def _get_paths(self, config: CollectionConfig) -> List[str]:
        """Get the appropriate paths for this extractor."""
        path_key = self.extractor.get_path_key()

        # Handle special cases for PDOS
        if config.is_pdos and path_key == "kpdos_output_paths":
            path_key = "pdos_output_paths"
        elif config.is_pdos and path_key == "scf_output_paths":
            path_key = "nscf_output_paths"

        return config.paths[path_key]

    def _process_single_case(self, path: str, config: CollectionConfig,
                             flag: str, soc_handler: SpinOrbitHandler) -> Optional[Any]:
        """Process a single case (SOC or non-SOC)."""
        data, success = self.extractor.extract_data(
            path, config.compound_name, flag, is_pdos=config.is_pdos
        )

        if not success:
            if soc_handler.handle_error(flag):
                return None  # Skip this case
        else:
            soc_handler.mark_found(flag)
            print_success(self.extractor.get_success_message())
            return data

        return None


class CollectorFactory:
    """Factory for creating data collectors."""

    @staticmethod
    def create_band_collector() -> DataCollector:
        extractor = SimpleDataExtractor(
            extractor_func=extract_band_number,
            path_key="pw_bands_output_paths",
            data_name="band numbers"
        )
        return DataCollector(extractor)

    @staticmethod
    def create_fermi_collector() -> DataCollector:
        extractor = SimpleDataExtractor(
            extractor_func=extract_fermi_energy,
            path_key="scf_output_paths",
            data_name="Fermi energies"
        )
        return DataCollector(extractor)

    @staticmethod
    def create_atomic_states_count_collector() -> DataCollector:
        extractor = SimpleDataExtractor(
            extractor_func=extract_number_of_atomic_states,
            path_key="kpdos_output_paths",
            data_name="number of atomic states"
        )
        return DataCollector(extractor)

    @staticmethod
    def create_atomic_states_info_collector() -> DataCollector:
        extractor = AtomicStatesExtractor("kpdos_output_paths")
        return DataCollector(extractor)


def collect_band_numbers(paths: Dict[str, List[str]],
                         compound_name: str,
                         spin_orbit_flags: List[str],
                         skip_soc: bool = False,
                         skip_normal: bool = False) -> list[int]:
    """
    Collect band numbers from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip SOC calculations
        skip_normal (bool): Whether to skip non-SOC calculations

    Returns:
        list: List of band numbers
    """
    config = CollectionConfig(
        paths=paths,
        compound_name=compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=skip_soc,
        skip_normal=skip_normal
    )

    collector = CollectorFactory.create_band_collector()
    return collector.collect(config)


def collect_fermi_energies(paths: Dict[str, List[str]],
                           compound_name: str,
                           spin_orbit_flags: List[str],
                           skip_soc: bool = False,
                           skip_normal: bool = False,
                           is_pdos: bool = False) -> List[float]:
    """
    Collect Fermi energies from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations
        skip_normal (bool): Whether to skip non-SOC calculations
        is_pdos (bool): Whether to collect Fermi energies from PDOS files

    Returns:
        list: List of Fermi energies
    """
    config = CollectionConfig(
        paths=paths,
        compound_name=compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=skip_soc,
        skip_normal=skip_normal,
        is_pdos=is_pdos
    )

    collector = CollectorFactory.create_fermi_collector()
    return collector.collect(config)



def collect_number_of_atomic_states(paths: Dict[str, List[str]],
                                    compound_name: str,
                                    spin_orbit_flags: List[str],
                                    skip_soc: bool = False,
                                    skip_normal: bool = False) -> List[int]:
    """
    Collect the number of atomic states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations
        skip_normal (bool): Whether to skip non-SOC calculations

    Returns:
        list: List of number of atomic states
    """
    config = CollectionConfig(
        paths=paths,
        compound_name=compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=skip_soc,
        skip_normal=skip_normal
    )

    collector = CollectorFactory.create_atomic_states_count_collector()
    return collector.collect(config)


def collect_atomic_states_info(paths: Dict[str, List[str]],
                               compound_name: str,
                               spin_orbit_flags: List[str],
                               skip_soc: bool = False,
                               skip_normal: bool = False,
                               is_pdos: bool = False) -> List[Dict[Any, Any]]:
    """
    Collect the atomic info states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations
        skip_normal (bool): Whether to skip non-SOC calculations
        is_pdos (bool): Whether to collect atomic states info from PDOS files

    Returns:
        list: A list of dictionaries containing the indices and orbital weights of each atomic state
    """
    config = CollectionConfig(
        paths=paths,
        compound_name=compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=skip_soc,
        skip_normal=skip_normal,
        is_pdos=is_pdos
    )

    collector = CollectorFactory.create_atomic_states_info_collector()
    return collector.collect(config)


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


# Test to ensure the module works as expected
if __name__ == "__main__":
    """
    Main entry point for testing the module.

    This script validates that the prepare_dft_info has executed successfully and prints the extracted 
    information if successful.
    """
    os.chdir("..")

    # Create the parser
    parser = argparse.ArgumentParser(description="Tests the data collector module.")

    # Add arguments
    parser.add_argument(
        "compound_name",
        type=str,
        help="Name of the compound (e.g., 'GaAs', 'SiO2')."
    )

    parser.add_argument(
        "--project-config",
        type=str,
        help="Path to a custom JSON project configuration file."
    )

    parser.add_argument(
        "--config-type",
        type=str,
        default="bands",
        choices=["bands", "pdos", "wannier"],
        help="Type of configuration to use (default: 'bands')."
    )

    args = parser.parse_args(argv[1:])

    print_info(f"\n{args.config_type} config type was chosen for collecting data.")

    match args.config_type:
        case "wannier":
            project = initialize_project(args.compound_name,
                                         args.project_config,
                                         args.config_type,
                                         is_input=False, is_wannier=True)
            prepare_wannier_info(project)
            is_wannier = True
            is_pdos = False

        case "bands":
            project = initialize_project(args.compound_name,
                                         args.project_config,
                                         args.config_type,
                                         is_input=False)
            prepare_bands_info(project)
            is_wannier = False
            is_pdos = False

        case "pdos":
            project = initialize_project(args.compound_name,
                                         args.project_config,
                                         args.config_type,
                                         is_input=False, is_pdos=True)
            prepare_pdos_info(project)
            is_wannier = False
            is_pdos = True
        case _:
            print_error(f"Invalid configuration type: {args.config_type}")
            exit(1)

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
