from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CompoundData:
    """Represents parsed compound information."""
    element_names: List[str]
    element_numbers: List[int]
    number_of_atoms: int
    atom_types: int
    atomic_labels: List[str]

    @classmethod
    def from_compound_name(cls, compound_name: str) -> 'CompoundData':
        """Create CompoundData from a compound name string."""
        import re
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
class ProjectSetup:
    """Represents the complete project setup."""
    compound_name: str
    project_dir: str
    pseudo_dir: str
    calculation_dirs: List[str]
    compound_data: CompoundData
    include_stress: bool
    stress_amounts: Optional[List[str]] = None
    rel_pseudo_dir: Optional[str] = None