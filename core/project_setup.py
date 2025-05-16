import os

from rich import box
from rich.table import Table

from data.models import CompoundData, ProjectSetup
from core.config import load_config
from core.input_handler import get_strain_amounts, get_pbands_type
from typing import List

from ui.ui_helpers import print_header, print_info, console, print_success


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
        is_pdos: bool = False
) -> ProjectSetup:
    """
    Initialize the project directory and parse compound information.

    Args:
        argv (list): Command-line arguments containing the compound name and POSCAR file path.
        is_input (bool): Flag indicating if the function is called for input file generation. Defaults to True.
        is_wannier (bool): Flag indicating if the function is called for Wannier comparison initialization. Defaults to False.
        is_pdos (bool): Flag indicating if the function is called for PDOS initialization. Defaults to False.

    Returns:
        ProjectSetup: An object containing the initialized project setup details.

    Raises:
        ProjectInitializationError: If parsing the compound name fails.
    """
    from core.path_handler import get_project_directory, create_directories, validate_command_line_args, \
        build_file_paths
    print('\n')
    print_header("Project Initialization")
    config = load_config()

    if is_input:
        # For input file generation
        compound_name, poscar_file = validate_command_line_args(argv, is_for_plot=False)
        stress_amounts = get_strain_amounts(is_input=True)
        include_stress = bool(stress_amounts)
    else:
        # For output/analysis
        compound_name = validate_command_line_args(argv, is_for_plot=True)
        include_stress = get_pbands_type() if (not is_wannier and not is_pdos) else False
        stress_amounts = get_strain_amounts() if include_stress else None

    try:
        print_info("Recognizing elements...\n")

        # Parse compound information from the compound name
        compound_data = CompoundData.from_compound_name(compound_name)

        # Create compound info table
        compound_table = Table(title="Compound Information", box=box.ROUNDED)
        compound_table.add_column("Property", style="cyan")
        compound_table.add_column("Value", style="green")

        compound_table.add_row("Total atoms", str(compound_data.number_of_atoms))
        compound_table.add_row("Distinct atom types", str(compound_data.atom_types))
        compound_table.add_row("Elements", ", ".join(compound_data.element_names))
        console.print(compound_table)

    except Exception as ex:
        raise ProjectInitializationError(f"Failed to parse compound name: {str(ex)}")

    # Get the project directory path
    project_dir = get_project_directory(compound_name)
    print_info(f"\nProject directory: {project_dir}")

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

        print_success("Project initialization completed successfully.\n")

        # Return the project setup details
        return ProjectSetup(
            compound_name=compound_name,
            project_dir=project_dir,
            pseudo_dir=os.path.abspath(os.path.join(project_dir, config.directory_structure["pseudo"])),
            calculation_dirs=calculation_dirs,
            compound_data=compound_data,
            include_stress=include_stress,
            stress_amounts=stress_amounts,
            rel_pseudo_dir=os.path.abspath(os.path.join(project_dir, config.directory_structure["pseudo_rel"])),
            input_paths=paths,
            poscar_file=os.path.abspath(poscar_file),
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

        print_success("Project analysis setup completed successfully.\n")

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