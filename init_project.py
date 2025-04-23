from sys import argv
from typing import Optional, List
from models import CompoundData, ProjectSetup
from config import load_config
from input_handler import get_strain_amounts
from path_handler import get_project_directory, create_directories, validate_command_line_args


class ProjectInitializationError(Exception):
    """Base exception for project initialization errors."""
    pass


def initialize_project(
        compound_name: str,
        include_stress: bool = False,
        stress_amounts: Optional[List[str]] = None
) -> ProjectSetup:

    """Initialize project directory and parse compound information."""
    print("Initializing...\n", flush=True)
    config = load_config()

    print("Recognizing elements...", flush=True)
    try:
        compound_data = CompoundData.from_compound_name(compound_name)
    except Exception as e:
        raise ProjectInitializationError(f"Failed to parse compound name: {str(e)}")

    print(f"Total number of atoms found: {compound_data.number_of_atoms}", flush=True)
    print(f"Number of distinct atom types found: {compound_data.atom_types}", flush=True)

    print("Recognized elements:", *compound_data.element_names)

    project_dir = get_project_directory(compound_name)
    print(f"Project directory: {project_dir}", flush=True)

    calculation_dirs = create_directories(
        project_dir,
        config.directory_structure,
        include_stress,
        stress_amounts
    )

    return ProjectSetup(
        compound_name=compound_name,
        project_dir=project_dir,
        calculation_dirs=calculation_dirs,
        compound_data=compound_data,
        include_stress=include_stress,
        stress_amounts=stress_amounts
    )


if __name__ == "__main__":
    if len(argv) < 3:
        print("Usage: python script.py <compound_name> <poscar_file>")
        exit(1)

    try:
        # Validate command-line arguments for input file generation
        compound_name, poscar_file = validate_command_line_args(argv)

        # Get the list of strain amounts for input files
        stress_amounts = get_strain_amounts(is_input=True)
        include_stress = True if stress_amounts else False

        project = initialize_project(compound_name, include_stress, stress_amounts)

        print("\nInitialization complete. Here's a summary:")
        print(f"  Compound: {project.compound_name}")
        print(f"  Project directory: {project.project_dir}")
        print(f"  Calculation directories: {project.calculation_dirs}")
        print(f"  Elements: {project.compound_data.element_names}")
        print(f"  Atomic labels: {project.compound_data.atomic_labels}")

    except ProjectInitializationError as e:
        print(f"Error during project initialization: {str(e)}")
        exit(1)

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        exit(1)
