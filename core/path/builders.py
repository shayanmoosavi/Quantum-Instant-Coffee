""" Module for building file paths for calculations.

This module provides classes for building file paths for various calculations in a project.

Classes:
    - FilePatternBuilder: Handles file pattern building and validation.
    - CalculationPathBuilder: Builds paths for specific calculation types based on predefined patterns.
"""
import os
from typing import Optional, Dict, List

from .exceptions import ProjectInitializationError
from .models import CalculationType
from ui.ui_helpers import print_warning


class FilePatternBuilder:
    """
    Handles file pattern building and validation.

    Attributes:
        file_patterns (Dict[str, str]): A dictionary mapping pattern keys to file patterns.
    """
    def __init__(self, file_patterns: Dict[str, str]):
        """
        Initializes the FilePatternBuilder with a dictionary of file patterns.

        Args:
            file_patterns (Dict[str, str]): A dictionary mapping pattern keys to file patterns.
        """
        self.file_patterns = file_patterns

    def build_file_path(self, base_path: str, compound_name: str,
                        pattern_key: str, flag: str = "") -> Optional[str]:
        """
        Builds a single file path based on the provided pattern key.

        Args:
            base_path (str): The base directory path.
            compound_name (str): The name of the compound.
            pattern_key (str): The key to retrieve the file pattern.
            flag (str): An optional flag to append to the filename (e.g., "_soc" for SOC calculations).

        Returns:
            Optional[str]: The constructed file path, or None if the pattern key is not found.

        Raises:
            KeyError: If the pattern key is not found in the file patterns.
        """
        try:
            pattern = self.file_patterns[pattern_key]
            filename = pattern.format(compound_name=compound_name, flag=flag)
            return os.path.join(base_path, filename)
        except KeyError:
            print_warning(f"Key '{pattern_key}' not found in file patterns. Skipping...")
            return None


class CalculationPathBuilder:
    """
    Builds paths for specific calculation types.

    Attributes:
        pattern_builder (FilePatternBuilder): An instance of FilePatternBuilder used for path construction.
        CALCULATION_FILE_MAPPING (Dict[CalculationType, Dict[str, List[str]]]):
            A mapping of calculation types to required input and output file keys.
    """

    # Define which file types each calculation needs
    CALCULATION_FILE_MAPPING = {
        CalculationType.SCF: {
            'input': ['relax_input', 'vc_relax_input', 'scf_input'],
            'output': ['scf_output']
        },
        CalculationType.SCF_SOC: {
            'input': ['relax_input', 'vc_relax_input', 'scf_input'],
            'output': ['scf_output']
        },
        CalculationType.PROJECTED_BANDS: {
            'input': ['pw_bands_input', 'kpdos_input', 'bands_input'],
            'output': ['pw_bands_output', 'kpdos_output', 'projbands_output', 'bands_gnu']
        },
        CalculationType.PROJECTED_BANDS_SOC: {
            'input': ['pw_bands_input', 'kpdos_input', 'bands_input'],
            'output': ['pw_bands_output', 'kpdos_output', 'projbands_output', 'bands_gnu']
        },
        CalculationType.PDOS: {
            'input': ['nscf_input', 'pdos_input'],
            'output': ['nscf_output', 'pdos_output']
        },
        CalculationType.PDOS_SOC: {
            'input': ['nscf_input', 'pdos_input'],
            'output': ['nscf_output', 'pdos_output']
        },
        CalculationType.WANNIER: {
            'input': ['nscf_wannier_input', 'pw2wan_input', 'wannier_input'],
            'output': ['nscf_wannier_output', 'wannier_bands', 'bands_gnu']
        },
        CalculationType.WANNIER_SOC: {
            'input': ['nscf_wannier_input', 'pw2wan_input', 'wannier_input'],
            'output': ['nscf_wannier_output', 'wannier_bands', 'bands_gnu']
        },
        CalculationType.STRAIN: {
            'input': ['scf_input', 'pw_bands_input', 'kpdos_input', 'bands_input'],
            'output': ['scf_output', 'pw_bands_output', 'kpdos_output', 'projbands_output', 'bands_gnu']
        }
    }

    def __init__(self, pattern_builder: FilePatternBuilder):
        """
        Initializes the CalculationPathBuilder with a FilePatternBuilder instance.

        Args:
            pattern_builder (FilePatternBuilder): An instance of FilePatternBuilder used for path construction.
        """
        self.pattern_builder = pattern_builder

    def build_paths_for_calculation(self, calc_type: CalculationType, base_path: str,
                                    compound_name: str, is_input: bool,
                                    stress_amounts: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Builds all paths for a specific calculation type.

        Args:
            calc_type (CalculationType): The type of calculation.
            base_path (str): The base directory path.
            compound_name (str): The name of the compound.
            is_input (bool): Flag indicating whether to build input or output paths.
            stress_amounts (Optional[List[str]]): A list of stress amounts for strain calculations. Defaults to None.

        Returns:
            Dict[str, List[str]]: A dictionary mapping file keys to lists of constructed file paths.

        Raises:
            ProjectInitializationError: If the calculation type is unsupported.
        """
        if calc_type not in self.CALCULATION_FILE_MAPPING:
            raise ProjectInitializationError(f"Unsupported calculation type: {calc_type}")

        file_type = 'input' if is_input else 'output'
        file_keys = self.CALCULATION_FILE_MAPPING[calc_type][file_type]
        flag = "_soc" if calc_type.is_soc else ""

        result = {}

        if calc_type == CalculationType.STRAIN and stress_amounts:
            # Handle strain calculations with multiple stress amounts
            for file_key in file_keys:
                result[file_key] = []
                for stress_amount in stress_amounts:
                    stress_path = os.path.join(base_path, stress_amount)
                    path = self.pattern_builder.build_file_path(
                        stress_path, compound_name, file_key, flag
                    )
                    if path:
                        result[file_key].append(path)
        else:
            # Handle regular calculations
            for file_key in file_keys:
                path = self.pattern_builder.build_file_path(
                    base_path, compound_name, file_key, flag
                )
                if path:
                    result[file_key] = [path]

        return result
