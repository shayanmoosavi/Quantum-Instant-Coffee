""" Models for path building context and calculation types.

This module defines the context and types used for building paths in the project.

Classes:
    - CalculationType: Enum representing different calculation types.
    - PathBuildingContext: Dataclass containing parameters needed for path building.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

from core.config import ProjectConfig


class CalculationType(Enum):
    """
    Enumeration of calculation types for better type safety.

    Attributes:
        SCF (str): Self-consistent field calculation.
        SCF_SOC (str): Self-consistent field calculation with spin-orbit coupling.
        PROJECTED_BANDS (str): Projected bands calculation.
        PROJECTED_BANDS_SOC (str): Projected bands calculation with spin-orbit coupling.
        PDOS (str): Projected density of states calculation.
        PDOS_SOC (str): Projected density of states calculation with spin-orbit coupling.
        WANNIER (str): Wannier function calculation.
        WANNIER_SOC (str): Wannier function calculation with spin-orbit coupling.
        STRAIN (str): Strain calculation.
        PSEUDO (str): Pseudopotential directory.
        PSEUDO_REL (str): Relativistic pseudopotential directory.
    """
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
        """
        Check if this calculation type uses spin-orbit coupling (SOC).

        Returns:
            bool: True if the calculation type includes SOC, False otherwise.
        """
        return "_soc" in self.value

    @property
    def base_type(self) -> str:
        """
        Get the base calculation type without the SOC suffix.

        Returns:
            str: The base calculation type.
        """
        return self.value.replace("_soc", "")


@dataclass
class PathBuildingContext:
    """
    Context object containing all parameters needed for path building.

    Attributes:
        project_dir (str): The root directory of the project.
        compound_name (str): The name of the compound being processed.
        config (ProjectConfig): The project configuration object.
        is_input (bool): Flag indicating whether paths are for input files. Defaults to True.
        include_stress (bool): Flag indicating whether stress calculations are included. Defaults to False.
        stress_amounts (Optional[List[str]]): List of stress amounts for strain calculations. Defaults to None.
        skip_soc (bool): Flag indicating whether to skip SOC calculations. Defaults to False.
        skip_normal (bool): Flag indicating whether to skip normal (non-SOC) calculations. Defaults to False.
    """
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
