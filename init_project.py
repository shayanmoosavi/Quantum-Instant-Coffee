"""Script for testing the initialization of a project based on a compound name and POSCAR file.

This script tests the initialization of the project based on the provided compound name and POSCAR file.
It handles command-line arguments, initializes the project, and provides a summary of the project configuration.

Usage:
    python script.py <compound_name> <poscar_file>

Args:
    compound_name (str): The name of the compound to initialize the project for.
    poscar_file (str): The path to the POSCAR file for the compound.

Raises:
    ProjectInitializationError: If an error occurs during project initialization.
    Exception: For any unexpected errors.
"""
from sys import argv
from project_setup import *

if __name__ == "__main__":
    """
    Main entry point for the script. Handles command-line arguments and initializes the project.

    Usage:
        python script.py <compound_name> <poscar_file>

    Args:
        compound_name (str): The name of the compound to initialize the project for.
        poscar_file (str): The path to the POSCAR file for the compound.

    Raises:
        ProjectInitializationError: If an error occurs during project initialization.
        Exception: For any unexpected errors.
    """
    try:
        # Determine if this is for input generation based on argument count
        is_input = len(argv) == 3

        is_wannier = input("Are you testing for Wannier initialization? (yes/no): ").strip().lower() == "yes"

        # Initialize and prepare project
        project = initialize_project(argv, is_input, is_wannier)

        # Print summary
        print("\nInitialization complete. Project information:")
        print(f"  Compound name: {project.compound_name}")
        print(f"  Project directory: {project.project_dir}")
        print(f"  Include stress: {project.include_stress}")
        if project.include_stress:
            print(f"  Stress amounts: {project.stress_amounts}")
        print(f"  Pseudopotential directory: {project.pseudo_dir}")
        print(f"  Relativistic Pseudopotential directory: {project.rel_pseudo_dir}")
        if is_input:
            print(f"  Calculation directories: {project.calculation_dirs}")
        print(f"  Elements: {project.compound_data.element_names}")
        print(f"  Atomic labels: {project.compound_data.atomic_labels}")

        if is_input:
            print("\nInput paths:")
            for path_type, paths in project.input_paths.items():
                print(f"{path_type}: {paths}")
        else:
            print("\nOutput paths:")
            for path_type, paths in project.output_paths.items():
                print(f"{path_type}: {paths}")

            print("\nChecking if the output files exist:")
            failure = False
            for paths in list(project.output_paths.values()):
                for path in paths:
                    exists = os.path.exists(path)
                    print(f"{'✓' if exists else '✗'} {path}")
                    failure = failure or not exists

            print("\nTest result:", "FAILED" if failure else "PASSED")

    except ProjectInitializationError as e:
        print(f"Error during project initialization: {str(e)}")
        exit(1)

    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        exit(1)
