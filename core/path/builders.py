import os
from typing import Optional, Dict, List

from core.path.exceptions import ProjectInitializationError
from core.path.models import CalculationType
from ui.ui_helpers import print_warning


class FilePatternBuilder:
    """Handles file pattern building and validation."""

    def __init__(self, file_patterns: Dict[str, str]):
        self.file_patterns = file_patterns

    def build_file_path(self, base_path: str, compound_name: str,
                        pattern_key: str, flag: str = "") -> Optional[str]:
        """Build a single file path from pattern."""
        try:
            pattern = self.file_patterns[pattern_key]
            filename = pattern.format(compound_name=compound_name, flag=flag)
            return os.path.join(base_path, filename)
        except KeyError:
            print_warning(f"Key '{pattern_key}' not found in file patterns. Skipping...")
            return None


class CalculationPathBuilder:
    """Builds paths for specific calculation types."""

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
            'output': ['nscf_wannier_output', 'wannier_bands']
        },
        CalculationType.WANNIER_SOC: {
            'input': ['nscf_wannier_input', 'pw2wan_input', 'wannier_input'],
            'output': ['nscf_wannier_output', 'wannier_bands']
        },
        CalculationType.STRAIN: {
            'input': ['scf_input', 'pw_bands_input', 'kpdos_input', 'bands_input'],
            'output': ['scf_output', 'pw_bands_output', 'kpdos_output', 'projbands_output', 'bands_gnu']
        }
    }

    def __init__(self, pattern_builder: FilePatternBuilder):
        self.pattern_builder = pattern_builder

    def build_paths_for_calculation(self, calc_type: CalculationType, base_path: str,
                                    compound_name: str, is_input: bool,
                                    stress_amounts: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """Build all paths for a specific calculation type."""
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
