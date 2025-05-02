import os
from data.models import CompoundData, ProjectSetup
from core.config import load_config
from core.input_handler import get_strain_amounts, get_pbands_type
from typing import List

class ProjectInitializationError(Exception):
    """
    Custom exception raised for errors during project initialization.

    Attributes:
        message (str): Explanation of the error.
    """
    pass

def initialize_project(
        argv: List[str],
        is_input: bool = True,
        is_wannier: bool = False,
) -> ProjectSetup:
    """
    Initialize the project directory and parse compound information.

    Args:
        argv (list): Command-line arguments containing the compound name and POSCAR file path.
        is_input (bool): Flag indicating if the function is called for input file generation. Defaults to True.
        is_wannier (bool): Flag indicating if the function is called for Wannier comparison initialization. Defaults to False.

    Returns:
        ProjectSetup: An object containing the initialized project setup details.

    Raises:
        ProjectInitializationError: If parsing the compound name fails.
    """
    from core.path_handler import get_project_directory, create_directories, validate_command_line_args, \
        build_file_paths

    print("Initializing...\n", flush=True)
    config = load_config()

    if is_input:
        # For input file generation
        compound_name, poscar_file = validate_command_line_args(argv, is_for_plot=False)
        stress_amounts = get_strain_amounts(is_input=True)
        include_stress = bool(stress_amounts)
    else:
        # For output/analysis
        compound_name = validate_command_line_args(argv, is_for_plot=True)
        include_stress = get_pbands_type() if not is_wannier else False
        stress_amounts = get_strain_amounts() if include_stress else None

    try:

        print("Recognizing elements...", flush=True)

        # Parse compound information from the compound name
        compound_data = CompoundData.from_compound_name(compound_name)

    except Exception as ex:
        raise ProjectInitializationError(f"Failed to parse compound name: {str(ex)}")

    print(f"Total number of atoms found: {compound_data.number_of_atoms}", flush=True)
    print(f"Number of distinct atom types found: {compound_data.atom_types}", flush=True)

    print("Recognized elements:", *compound_data.element_names)

    # Get the project directory path
    project_dir = get_project_directory(compound_name)
    print(f"Project directory: {project_dir}", flush=True)

    if is_input:
        # Create the required calculation directories
        calculation_dirs = create_directories(
            project_dir,
            config.directory_structure,
            include_stress,
            stress_amounts
        )

        paths = build_file_paths(project_dir,
                                 compound_name,
                                 config,
                                 is_input,
                                 include_stress,
                                 stress_amounts)

        # Return the project setup details
        return ProjectSetup(
            compound_name=compound_name,
            project_dir=project_dir,
            pseudo_dir=os.path.abspath(config.directory_structure["pseudo"]),
            calculation_dirs=calculation_dirs,
            compound_data=compound_data,
            include_stress=include_stress,
            stress_amounts=stress_amounts,
            rel_pseudo_dir=os.path.abspath(config.directory_structure["pseudo_rel"]),
            input_paths=paths,
            poscar_file=poscar_file,
            skip_soc=True if include_stress else False
        )

    else:
        # For output/analysis, return the project setup details
        paths, skip_soc = build_file_paths(project_dir,
                                 compound_name,
                                 config,
                                 is_input,
                                 include_stress,
                                 stress_amounts)

        return ProjectSetup(
            compound_name=compound_name,
            project_dir=project_dir,
            pseudo_dir=os.path.abspath(config.directory_structure["pseudo"]),
            calculation_dirs=[],
            compound_data=compound_data,
            include_stress=include_stress,
            stress_amounts=stress_amounts,
            rel_pseudo_dir=os.path.abspath(config.directory_structure["pseudo_rel"]),
            output_paths=paths,
            skip_soc=skip_soc
        )