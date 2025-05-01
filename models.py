"""
Data models for quantum material calculations.

This module defines the core data structures used throughout the project for
handling compound information, DFT calculation results, and project configuration.

Classes:
    CompoundData: Parses and stores chemical compound information.
    DFTInfo: Container for DFT calculation results.
    ProjectSetup: Main project configuration and data storage.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from numpy import ndarray

@dataclass
class CompoundData:
    """Represents parsed compound information.

    Attributes:
        element_names (List[str]): Names of the elements in the compound.
        element_numbers (List[int]): Number of atoms for each element in the compound.
        number_of_atoms (int): Total number of atoms in the compound.
        atom_types (int): Number of unique element types in the compound.
        atomic_labels (List[str]): List of atomic labels for all atoms in the compound.
    """
    element_names: List[str]
    element_numbers: List[int]
    number_of_atoms: int
    atom_types: int
    atomic_labels: List[str]

    @classmethod
    def from_compound_name(cls, compound_name: str) -> 'CompoundData':
        """Create CompoundData from a compound name string.

        Args:
            compound_name (str): The chemical formula of the compound (e.g., "H2O", "C6H12O6").

        Returns:
            CompoundData: An instance of CompoundData with parsed information.

        Raises:
            ValueError: If the compound name is invalid or cannot be parsed.
        """
        pattern = r"([A-Z][a-z]?)(\d*)"
        matches = re.compile(pattern).finditer(compound_name)

        element_names = []
        element_numbers = []

        for match in matches:
            element_names.append(match.group(1))
            element_numbers.append(int(match.group(2) or 1))

        number_of_atoms = sum(element_numbers)
        atom_types = len(element_names)

        atomic_labels = [
            element_name
            for element_name, element_number in zip(element_names, element_numbers)
            for _ in range(element_number)
        ]

        return cls(
            element_names=element_names,
            element_numbers=element_numbers,
            number_of_atoms=number_of_atoms,
            atom_types=atom_types,
            atomic_labels=atomic_labels
        )

@dataclass
class DFTInfo:
    """
    Container for DFT (Density Functional Theory) calculation results.

    Attributes:
        number_of_bands (List[int]): Number of bands for each calculation.
        fermi_energies (List[float]): Fermi energy values for each calculation.
        number_of_atomic_states (List[int]): Number of atomic states for each calculation.
        atomic_states_info (List[Dict[str, Any]]): Detailed information about atomic states.
        spin_orbit_flags (List[str]): Flags indicating spin-orbit coupling for each calculation.
    """

    number_of_bands: List[int]
    fermi_energies: List[float]
    number_of_atomic_states: List[int]
    atomic_states_info: List[Dict[str, Any]]
    spin_orbit_flags: List[str]

@dataclass
class BandData:
    """Container for band structure calculation data.

    Attributes:
        projbands_data (List[ndarray]): Projected bands data for each calculation
        k_points_proj (List[ndarray]): K-points for projected bands
        k_points (List[ndarray]): K-points for regular bands
        energy_proj (List[ndarray]): Energy values for projected bands
        energy (List[ndarray]): Energy values for regular bands
        atomic_projection_weights (List[Dict]): Orbital weights for each calculation
        atomic_projections (List[str]): List of atomic projections
        unique_elements (List[str]): List of unique elements in the projections
    """
    projbands_data: List[ndarray]
    k_points_proj: List[ndarray]
    k_points: List[ndarray]
    energy_proj: List[ndarray]
    energy: List[ndarray]
    atomic_projection_weights: List[Dict]
    atomic_projections: List[str]
    unique_elements: List[str]

@dataclass
class WannierSetup:
    """Configuration for Wannier calculations.

    Attributes:
        fermi_energies: List of Fermi energies
        alat_parameters: List of lattice parameters
        skip_normal: Whether to skip non-SOC calculations
        comparison_data: Wannier and DFT data for comparison
    """
    fermi_energies: List[float]
    alat_parameters: List[float]
    skip_normal: bool = False
    comparison_data: Dict[str, List[ndarray]] = None


@dataclass
class ProjectSetup:
    """Represents the complete project setup.

    Attributes:
        compound_name (str): Name of the compound being analyzed.
        project_dir (str): Path to the project directory.
        pseudo_dir (str): Path to the pseudopotential directory.
        calculation_dirs (List[str]): List of directories for calculations.
        compound_data (CompoundData): Parsed compound information.
        include_stress (bool): Whether strain analysis is included.
        stress_amounts (Optional[List[str]]): List of stress amounts, if applicable.
        rel_pseudo_dir (Optional[str]): Path to the relativistic pseudopotential directory.
        poscar_file (Optional[str]): Path to the POSCAR file, if applicable.
        dft_info (Optional[DFTInfo]): DFT calculation results, if available.
        input_paths (Optional[Dict[str, List[str]]]): Paths for input files, if applicable.
        output_paths (Optional[Dict[str, List[str]]]): Paths for output files, if applicable.
        skip_soc (bool): Whether spin-orbit coupling is skipped.
    """
    compound_name: str
    project_dir: str
    pseudo_dir: str
    calculation_dirs: List[str]
    compound_data: CompoundData
    include_stress: bool
    stress_amounts: Optional[List[str]] = None
    rel_pseudo_dir: Optional[str] = None
    poscar_file: Optional[str] = None
    dft_info: Optional[DFTInfo] = None
    band_data: Optional[BandData] = None
    wannier_setup: Optional[WannierSetup] = None
    input_paths: Optional[Dict[str, List[str]]] = None
    output_paths: Optional[Dict[str, List[str]]] = None
    skip_soc: bool = False

    def add_dft_info(self, dft_info: DFTInfo) -> None:
        """Add DFT calculation results to the project setup.

        Args:
            dft_info (DFTInfo): The DFT calculation results to add.
        """
        self.dft_info = dft_info

    def add_wannier_setup(self, wannier_setup: WannierSetup) -> None:
        """Add Wannier calculation setup to the project setup.

        Args:
            wannier_setup (WannierSetup): The Wannier calculation setup to add.
        """
        self.wannier_setup = wannier_setup