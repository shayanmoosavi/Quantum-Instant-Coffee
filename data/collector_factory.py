""" Factory for creating data collectors for Quantum ESPRESSO output files.

This module provides a factory for creating various data collectors used to extract
information from Quantum ESPRESSO output files. The factory simplifies the creation
of collectors by encapsulating the initialization logic for different types of data
extraction tasks.

Classes:
    SpinOrbitHandler: A class to handle spin-orbit coupling (SOC) related logic.
    CollectionConfig: Configuration for data collection operations.
    DataCollector: A template method class for collecting data from Quantum ESPRESSO files.
    WannierCollector: A specialized collector for Wannier data.
    CollectorFactory: A factory class for creating data collectors.

Usage:
    - Use `CollectorFactory.create_band_collector()` to create a collector for band numbers.
    - Use `CollectorFactory.create_fermi_collector()` to create a collector for Fermi energies.
    - Use `CollectorFactory.create_atomic_states_count_collector()` to create a collector for the number of atomic states.
    - Use `CollectorFactory.create_atomic_states_info_collector()` to create a collector for atomic states information.
    - Use `CollectorFactory.create_wannier_collector()` to create a collector for Wannier data.
"""
from dataclasses import dataclass
from typing import List, Any, Dict, Optional, Tuple

from data.data_extractor import DataExtractor, AtomicStatesExtractor, SimpleDataExtractor, WannierDataExtractor
from ui.ui_helpers import print_info, prompt_input, print_error, console, print_success
from utils.file_parser import extract_band_number, extract_fermi_energy, extract_number_of_atomic_states


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
    """
    Template method class for collecting data from Quantum ESPRESSO files.

    Attributes:
        extractor (DataExtractor): The data extractor used for extracting data from files.
    """

    def __init__(self, extractor: DataExtractor):
        """
        Initializes the DataCollector with a specific data extractor.

        Args:
            extractor (DataExtractor): The data extractor to be used for data collection.
        """
        self.extractor = extractor

    def collect(self, config: CollectionConfig) -> List[Any]:
        """
        Collects data based on the provided configuration.

        Args:
            config (CollectionConfig): Configuration for data collection.

        Returns:
            List[Any]: A list of collected data.
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
        """
        Retrieves the appropriate paths for the extractor.

        Args:
            config (CollectionConfig): Configuration for data collection.

        Returns:
            List[str]: A list of file paths.
        """
        path_key = self.extractor.get_path_key()

        # Handle special cases for PDOS
        if config.is_pdos and path_key == "kpdos_output_paths":
            path_key = "pdos_output_paths"
        elif config.is_pdos and path_key == "scf_output_paths":
            path_key = "nscf_output_paths"

        return config.paths[path_key]

    def _process_single_case(self, path: str, config: CollectionConfig,
                             flag: str, soc_handler: SpinOrbitHandler) -> Optional[Any]:
        """
        Processes a single case (SOC or non-SOC) during data collection.

        Args:
            path (str): Path to the file.
            config (CollectionConfig): Configuration for data collection.
            flag (str): Flag indicating SOC or non-SOC case.
            soc_handler (SpinOrbitHandler): Handler for SOC-related logic.

        Returns:
            Optional[Any]: Collected data for the case, or None if the case is skipped.
        """
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
    """
    Template method class for collecting Wannier data from Quantum ESPRESSO files.

    Attributes:
        soc_handler (SpinOrbitHandler): Handler for SOC-related logic.
    """

    def __init__(self, extractor: DataExtractor):
        """
        Initializes the WannierCollector with a specific data extractor.

        Args:
            extractor (DataExtractor): The data extractor to be used for Wannier data collection.
        """
        super().__init__(extractor)
        self.soc_handler = None  # Will be set during collection

    def collect(self, config: CollectionConfig) -> Tuple[List[float], List[float]]:
        """
        Collects Wannier data and returns separate lists for alat and Fermi energies.

        Args:
            config (CollectionConfig): Configuration for data collection.

        Returns:
            Tuple[List[float], List[float]]: A tuple containing lists of alat parameters and Fermi energies.
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
    """
    Factory for creating data collectors.

    Methods:
        create_band_collector(): Creates a collector for band numbers.
        create_fermi_collector(): Creates a collector for Fermi energies.
        create_atomic_states_count_collector(): Creates a collector for the number of atomic states.
        create_atomic_states_info_collector(): Creates a collector for atomic states information.
        create_wannier_collector(): Creates a collector for Wannier data.
    """

    @staticmethod
    def create_band_collector() -> DataCollector:
        """
        Creates a collector for band numbers.

        Returns:
            DataCollector: A collector for band numbers.
        """
        extractor = SimpleDataExtractor(
            extractor_func=extract_band_number,
            path_key="pw_bands_output_paths",
            data_name="band numbers"
        )
        return DataCollector(extractor)

    @staticmethod
    def create_fermi_collector() -> DataCollector:
        """
        Creates a collector for Fermi energies.

        Returns:
            DataCollector: A collector for Fermi energies.
        """
        extractor = SimpleDataExtractor(
            extractor_func=extract_fermi_energy,
            path_key="scf_output_paths",
            data_name="Fermi energies"
        )
        return DataCollector(extractor)

    @staticmethod
    def create_atomic_states_count_collector() -> DataCollector:
        """
        Creates a collector for the number of atomic states.

        Returns:
            DataCollector: A collector for the number of atomic states.
        """
        extractor = SimpleDataExtractor(
            extractor_func=extract_number_of_atomic_states,
            path_key="kpdos_output_paths",
            data_name="number of atomic states"
        )
        return DataCollector(extractor)

    @staticmethod
    def create_atomic_states_info_collector() -> DataCollector:
        """
        Creates a collector for atomic states information.

        Returns:
            DataCollector: A collector for atomic states information.
        """
        extractor = AtomicStatesExtractor("kpdos_output_paths")
        return DataCollector(extractor)

    @staticmethod
    def create_wannier_collector() -> WannierCollector:
        """
        Creates a collector for Wannier data.

        Returns:
            WannierCollector: A collector for Wannier data.
        """
        extractor = WannierDataExtractor()
        return WannierCollector(extractor)
