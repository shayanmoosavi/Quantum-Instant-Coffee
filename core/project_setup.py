import os

from rich import box
from rich.table import Table

from data.models import CompoundData, ProjectSetup
from core.config_handler import load_project_config
from core.input_handler import get_strain_amounts, get_pbands_type
from typing import Optional, Dict

from ui.ui_helpers import print_header, print_info, console, print_success


class ProjectInitializationError(Exception):
    """
    Custom exception raised for errors during project initialization.

    Attributes:
        message (str): Explanation of the error.
    """
    pass


def has_soc_directories(directory_structure: Dict[str, str]) -> bool:
    """
    Check if the configuration contains SOC-related directories.

    Args:
        directory_structure (Dict[str, str]): A dictionary where keys are directory names
            and values are their corresponding paths.

    Returns:
        bool: True if SOC directories are present, False otherwise.
    """
    soc_dirs = {
        "scf_soc",
        "projected_bands_soc",
        "pdos_soc",
        "pseudo_rel"
    }

    return bool(soc_dirs & set(directory_structure.keys()))

def initialize_project(
        compound_name: str,
        config_file: str = None,
        config_type: str = "default",
        poscar_file: Optional[str] = None,
        is_input: bool = True,
        is_wannier: bool = False,
        is_pdos: bool = False
) -> ProjectSetup:
    """
    Initialize the project directory and parse compound information.

    Args:
        compound_name (str): The name of the compound (e.g., "SiO2").
        config_file (str): Path to the JSON configuration file. Defaults to None.
        config_type (str): Type of config, either 'default', 'bands', 'pdos', or 'wannier'.
        poscar_file (str): Path to the POSCAR file. Only used if is_input is True.
        is_input (bool): Flag indicating if the function is called for input file generation. Defaults to True.
        is_wannier (bool): Flag indicating if the function is called for Wannier comparison initialization. Defaults to False.
        is_pdos (bool): Flag indicating if the function is called for PDOS initialization. Defaults to False.

    Returns:
        ProjectSetup: An object containing the initialized project setup details.

    Raises:
        ProjectInitializationError: If parsing the compound name fails.
    """
    from core.path_handler import get_project_directory, create_directories, build_file_paths
    print('\n')
    print_header("Project Initialization")
    config = load_project_config(config_file, config_type)

    # Detect if SOC directories are available in config
    soc_available = has_soc_directories(config.directory_structure)
    print(f"Soc available: {soc_available}")
    # Determine skip_soc flag
    if not soc_available:
        # No SOC directories in config, automatically skip SOC
        skip_soc = True
        print_info("No SOC directories found in configuration. SOC calculations will be skipped.")
    else:
        # SOC directories are available, let SpinOrbitHandler manage user prompts
        skip_soc = False

    if is_input:
        # For input file generation
        if not poscar_file:
            raise ProjectInitializationError("POSCAR file is required for input file generation.")
        stress_amounts = get_strain_amounts(is_input=True) if "strain" in config.directory_structure else None
        include_stress = bool(stress_amounts)
    else:
        # For output/analysis
        include_stress = get_pbands_type() if (
                (not is_wannier and not is_pdos) and ("strain" in config.directory_structure)
        ) else False
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
            rel_pseudo_dir=os.path.abspath(
                os.path.join(
                    project_dir, config.directory_structure["pseudo_rel"])
            ) if skip_soc else None,
            input_paths=paths,
            poscar_file=os.path.abspath(poscar_file),
            skip_soc=True if include_stress or skip_soc else False
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
            pseudo_dir=os.path.abspath(os.path.join(project_dir, config.directory_structure["pseudo"])),
            calculation_dirs=[],
            compound_data=compound_data,
            include_stress=include_stress,
            stress_amounts=stress_amounts,
            rel_pseudo_dir=os.path.abspath(
                os.path.join(
                    project_dir, config.directory_structure["pseudo_rel"])
            ) if skip_soc else None,
            output_paths=paths,
            skip_soc=skip_soc
        )
