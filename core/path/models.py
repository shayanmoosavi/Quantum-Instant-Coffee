from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

from core.project_config import ProjectConfig


class CalculationType(Enum):
    """Enumeration of calculation types for better type safety."""
    SCF = "scf"
    SCF_SOC = "scf_soc"
    PROJECTED_BANDS = "projected_bands"
    PROJECTED_BANDS_SOC = "projected_bands_soc"
    PDOS = "pdos"
    PDOS_SOC = "pdos_soc"
    WANNIER = "wannier"
    WANNIER_SOC = "wannier_soc"
    STRAIN = "strain"
    PSEUDO = "pseudo"
    PSEUDO_REL = "pseudo_rel"

    @property
    def is_soc(self) -> bool:
        """Check if this calculation type uses SOC."""
        return "_soc" in self.value

    @property
    def base_type(self) -> str:
        """Get the base calculation type without SOC suffix."""
        return self.value.replace("_soc", "")


@dataclass
class PathBuildingContext:
    """Context object containing all parameters needed for path building."""
    project_dir: str
    compound_name: str
    config: ProjectConfig
    is_input: bool = True
    include_stress: bool = False
    stress_amounts: Optional[List[str]] = None
    skip_soc: bool = False
    skip_normal: bool = False

    def should_include_calculation(self, calc_type: CalculationType) -> bool:
        """
        Determine if a calculation should be included based on SOC and normal flags.

        Args:
            calc_type (str): The calculation type (e.g., 'scf', 'scf_soc', 'strain').

        Returns:
            bool: True if the calculation should be included, False otherwise.
        """
        # Pseudo directories are always excluded
        if calc_type in [CalculationType.PSEUDO, CalculationType.PSEUDO_REL]:
            return False

        # It's unnecessary to check for strain directory if stress is not included
        if calc_type == CalculationType.STRAIN and not self.include_stress:
            return False

        # Apply SOC/normal filtering
        if self.skip_soc and calc_type.is_soc:
            return False
        if self.skip_normal and not calc_type.is_soc:
            return False

        # If stress is included, we should not include SOC calculations
        if self.include_stress and calc_type.is_soc:
            return False

        return True
