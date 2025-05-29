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
    prepare_bands_info: Prepares band structure information by extracting data from output files.
    prepare_wannier_info: Prepares Wannier information by extracting data from NSCF Wannier output files.
    prepare_pdos_info: Prepares PDOS information by extracting data from output files.
"""
import argparse
from dataclasses import dataclass
from sys import argv
from typing import Any, Optional

from data.data_extractor import DataExtractor, SimpleDataExtractor, AtomicStatesExtractor, WannierDataExtractor
from data.data_generator import generate_pdos, generate_projected_bands
from ui.display_data import display_dft_info, display_atomic_states, display_wannier_info
from ui.ui_helpers import prompt_input, print_header
from utils.file_parser import *
from core.project_setup import initialize_project
from data.models import BandInfo, WannierSetup, ProjectSetup, DOSSetup
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


@dataclass
class CollectionConfig:
    """
    Configuration for data collection operations.

    Attributes:
        paths (Dict[str, List[str]]): Dictionary containing file paths for data collection.
        compound_name (str): Name of the compound being analyzed.
        spin_orbit_flags (List[str]): List of flags indicating spin-orbit coupling cases (e.g., "_soc").
        skip_soc (bool): Whether to skip spin-orbit coupling cases. Defaults to False.
        skip_normal (bool): Whether to skip non-spin-orbit coupling cases. Defaults to False.
        is_pdos (bool): Whether the data collection involves PDOS files. Defaults to False.
    """
    paths: Dict[str, List[str]]
    compound_name: str
    spin_orbit_flags: List[str]
    skip_soc: bool = False
    skip_normal: bool = False
    is_pdos: bool = False


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


class WannierCollector(DataCollector):
    """Template method class for collecting Wannier data from Quantum ESPRESSO files."""

    def __init__(self, extractor: DataExtractor):
        super().__init__(extractor)
        self.soc_handler = None  # Will be set during collection

    def collect(self, config: CollectionConfig) -> Tuple[List[float], List[float]]:
        """
        Collect Wannier data and return separate lists for alat and Fermi energies.

        Returns:
            Tuple of (alat_parameters, fermi_energies)
        """
        self.soc_handler = SpinOrbitHandler(config.skip_soc, config.skip_normal)
        alat_parameters = []
        fermi_energies = []

        # Get the appropriate paths based on the extractor
        paths = self._get_paths(config)

        for path, flag in zip(paths, config.spin_orbit_flags):
            if self.soc_handler.should_skip(flag):
                continue

            result = self._process_single_case(path, config, flag, self.soc_handler)
            if result is not None:
                alat, fermi_energy = result
                alat_parameters.append(alat)
                fermi_energies.append(fermi_energy)

        # Validate that at least one case was successful
        self.soc_handler.validate_at_least_one_case()
        return alat_parameters, fermi_energies


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

    @staticmethod
    def create_wannier_collector() -> WannierCollector:
        extractor = WannierDataExtractor()
        return WannierCollector(extractor)


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

    spin_orbit_flags = ["", "_soc"]

    config = CollectionConfig(
        paths=project.output_paths,
        compound_name=project.compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=project.skip_soc,
        skip_normal=False
    )

    # Collect Wannier parameters using the factory pattern
    collector = CollectorFactory.create_wannier_collector()

    try:
        alat_parameters, fermi_energies = collector.collect(config)

        wannier_setup = WannierSetup(
            fermi_energies=fermi_energies,
            alat_parameters=alat_parameters,
            skip_normal=collector.soc_handler.skip_normal,
            skip_soc=collector.soc_handler.skip_soc
        )

        # Add Wannier setup to project configuration
        project.add_wannier_setup(wannier_setup)
        return project

    except Exception as e:
        raise ProjectInitializationError(f"Failed to prepare Wannier info: {str(e)}")


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
