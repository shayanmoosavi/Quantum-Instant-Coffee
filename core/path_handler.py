"""Module for managing file paths.

This module provides functions to handle file paths for Quantum ESPRESSO calculations.
It includes functionality for validating command-line arguments, creating directory structures,
and building structured file paths for input and output files.
"""
import argparse
import os
from dataclasses import dataclass
from enum import Enum
from sys import argv
from typing import List, Dict, Optional

from core.config_handler import ProjectConfig, load_project_config
from core.input_handler import get_strain_amounts, get_pbands_type
from data.models import CompoundData, ProjectSetup
from ui.ui_helpers import *


class ProjectInitializationError(Exception):
    """
    Custom exception raised for errors during project initialization.

    Attributes:
        message (str): Explanation of the error.
    """
    pass


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


class DirectoryManager:
    """Manages directory creation and validation."""

    def __init__(self, project_dir: str):
        self.project_dir = project_dir

    def create_project_directories(self, context: PathBuildingContext) -> List[str]:
        """Create all required directories for the project."""
        from ui.ui_helpers import print_success, print_error, print_header, console, Table

        try:
            os.makedirs(self.project_dir, exist_ok=True)
            print_success(f"\nProject directory initialized at:\n {self.project_dir}\n")

            os.chdir(self.project_dir)
            created_dirs = []

            table = Table(title="Directory Creation Progress")
            table.add_column("Calculation Type", style="cyan")
            table.add_column("Status")

            print_header("Directory Creation")
            print('\n')

            for calc_name, dir_path in context.config.directory_structure.items():
                try:
                    calc_type = CalculationType(calc_name)
                except ValueError:
                    raise ProjectInitializationError("Invalid calculation type in directory structure.")

                if not context.should_include_calculation(calc_type):
                    continue

                # Skip pseudopotential directories
                if calc_type in [CalculationType.PSEUDO, CalculationType.PSEUDO_REL]:
                    continue

                if calc_type == CalculationType.STRAIN and not context.include_stress:
                    continue

                try:
                    if context.include_stress and calc_type == CalculationType.STRAIN:
                        for stress_amount in context.stress_amounts:
                            stress_path = os.path.join(dir_path, stress_amount)
                            os.makedirs(stress_path, exist_ok=True)
                            created_dirs.append(os.path.abspath(stress_path))
                            table.add_row(f"strain_{stress_amount}", "[green]✓ Created[/green]")
                    else:
                        os.makedirs(dir_path, exist_ok=True)
                        created_dirs.append(os.path.abspath(dir_path))
                        table.add_row(calc_name, "[green]✓ Created[/green]")

                except OSError as e:
                    table.add_row(calc_name, "[bold red]✗ Failed[/bold red]")
                    print_error(f"Error creating directory: \n{str(e)}")

            console.print(table)
            print_success("\nSuccessfully created calculation directories.\n")

            # Return to script root directory
            script_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            os.chdir(script_root_dir)

            return created_dirs

        except OSError as e:
            print_error(f"Error creating directories: {e}")
            return []


class StructuredPathOrganizer:
    """Organizes paths into the structured format expected by the application."""

    INPUT_PATH_KEYS = [
        "relax_input_paths", "vc_relax_input_paths", "scf_input_paths",
        "pw_bands_input_paths", "kpdos_input_paths", "bands_input_paths",
        "nscf_input_paths", "pdos_input_paths", "nscf_wannier_input_paths",
        "pw2wan_input_paths", "wannier_input_paths"
    ]

    OUTPUT_PATH_KEYS = [
        "scf_output_paths", "pw_bands_output_paths", "kpdos_output_paths",
        "projbands_paths", "bands_paths", "nscf_output_paths",
        "pdos_output_paths", "nscf_wannier_output_paths", "wannier_bands_paths"
    ]

    def organize_paths(self, raw_paths: Dict[str, Dict[str, List[str]]],
                       context: PathBuildingContext) -> Dict[str, List[str]]:
        """Organize raw paths into structured format."""
        if context.is_input:
            return self._organize_input_paths(raw_paths, context)
        else:
            return self._organize_output_paths(raw_paths, context)

    def _organize_input_paths(self, raw_paths: Dict[str, Dict[str, List[str]]],
                              context: PathBuildingContext) -> Dict[str, List[str]]:
        """Organize input paths."""
        structured = {key: [] for key in self.INPUT_PATH_KEYS}

        # Remove wannier paths if stress is included
        if context.include_stress:
            for key in ["nscf_wannier_input_paths", "pw2wan_input_paths", "wannier_input_paths"]:
                structured.pop(key, None)

        for calc_name, file_paths in raw_paths.items():
            try:
                calc_type = CalculationType(calc_name)
            except ValueError:
                continue

            self._add_input_paths_for_calculation(structured, calc_type, file_paths, context)

        return {key: value for key, value in structured.items() if value}

    def _organize_output_paths(self, raw_paths: Dict[str, Dict[str, List[str]]],
                               context: PathBuildingContext) -> Dict[str, List[str]]:
        """Organize output paths."""
        structured = {key: [] for key in self.OUTPUT_PATH_KEYS}

        for calc_name, file_paths in raw_paths.items():
            try:
                calc_type = CalculationType(calc_name)
            except ValueError:
                continue

            self._add_output_paths_for_calculation(structured, calc_type, file_paths, context)

        return {key: value for key, value in structured.items() if value}

    @staticmethod
    def _add_output_paths_for_calculation(structured: Dict[str, List[str]],
                                          calc_type: CalculationType,
                                          file_paths: Dict[str, List[str]],
                                          context: PathBuildingContext):
        """Add output paths for a specific calculation."""
        if calc_type in [CalculationType.SCF, CalculationType.SCF_SOC]:
            if not (context.include_stress and calc_type.is_soc):
                if "scf_output" in file_paths:
                    structured["scf_output_paths"].extend(file_paths["scf_output"])

        elif calc_type == CalculationType.STRAIN and context.include_stress:
            path_mapping = {
                "scf_output": "scf_output_paths",
                "pw_bands_output": "pw_bands_output_paths",
                "kpdos_output": "kpdos_output_paths",
                "projbands_output": "projbands_paths",
                "bands_gnu": "bands_paths"
            }
            for file_type, struct_key in path_mapping.items():
                if file_type in file_paths:
                    structured[struct_key].extend(file_paths[file_type])

        elif calc_type in [CalculationType.PDOS, CalculationType.PDOS_SOC]:
            if not (context.include_stress and calc_type.is_soc):
                for path_type in ["nscf_output", "pdos_output"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif calc_type in [CalculationType.WANNIER, CalculationType.WANNIER_SOC]:
            if not context.include_stress:
                for path_type in ["nscf_wannier_output", "wannier_bands"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif not (context.include_stress and calc_type.is_soc) and calc_type not in [
            CalculationType.PDOS, CalculationType.PDOS_SOC,
            CalculationType.WANNIER, CalculationType.WANNIER_SOC
        ]:
            path_mapping = {
                "pw_bands_output": "pw_bands_output_paths",
                "kpdos_output": "kpdos_output_paths",
                "projbands_output": "projbands_paths",
                "bands_gnu": "bands_paths"
            }
            for file_type, struct_key in path_mapping.items():
                if file_type in file_paths:
                    structured[struct_key].extend(file_paths[file_type])

    @staticmethod
    def _add_input_paths_for_calculation(structured: Dict[str, List[str]],
                                         calc_type: CalculationType,
                                         file_paths: Dict[str, List[str]],
                                         context: PathBuildingContext):
        """Add input paths for a specific calculation."""
        if calc_type in [CalculationType.SCF, CalculationType.SCF_SOC]:
            if not (context.include_stress and calc_type.is_soc):
                for path_type in ["relax_input", "vc_relax_input", "scf_input"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif calc_type == CalculationType.STRAIN and context.include_stress:
            for path_type in ["scf_input", "pw_bands_input", "kpdos_input", "bands_input"]:
                if path_type in file_paths:
                    structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif calc_type in [CalculationType.PDOS, CalculationType.PDOS_SOC]:
            if not (context.include_stress and calc_type.is_soc):
                for path_type in ["nscf_input", "pdos_input"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif calc_type in [CalculationType.WANNIER, CalculationType.WANNIER_SOC]:
            if not context.include_stress:
                for path_type in ["nscf_wannier_input", "pw2wan_input", "wannier_input"]:
                    if path_type in file_paths and file_paths[path_type]:
                        structured[f"{path_type}_paths"].extend(file_paths[path_type])

        elif not (context.include_stress and calc_type.is_soc) and calc_type not in [
            CalculationType.WANNIER, CalculationType.WANNIER_SOC
        ]:
            for path_type in ["pw_bands_input", "kpdos_input", "bands_input"]:
                if path_type in file_paths and file_paths[path_type]:
                    structured[f"{path_type}_paths"].extend(file_paths[path_type])


class PathManager:
    """Main class that coordinates all path-related operations."""

    def __init__(self):
        self.pattern_builder = None
        self.calc_path_builder = None
        self.directory_manager = None
        self.path_organizer = StructuredPathOrganizer()

    def build_file_paths(self, context: PathBuildingContext) -> Dict[str, List[str]]:
        """Main method to build file paths based on context."""
        # Initialize builders
        file_patterns = context.config.file_patterns.input if context.is_input else context.config.file_patterns.output
        self.pattern_builder = FilePatternBuilder(file_patterns)
        self.calc_path_builder = CalculationPathBuilder(self.pattern_builder)

        # Build raw paths
        raw_paths = {}
        for calc_name, dir_path in context.config.directory_structure.items():
            try:
                calc_type = CalculationType(calc_name)
            except ValueError:
                raise ProjectInitializationError("Invalid calculation type in directory structure.")

            if not context.should_include_calculation(calc_type):
                continue

            if calc_type in [CalculationType.PSEUDO, CalculationType.PSEUDO_REL]:
                continue

            if calc_type == CalculationType.STRAIN and not context.include_stress:
                continue

            base_path = os.path.join(context.project_dir, dir_path)
            paths = self.calc_path_builder.build_paths_for_calculation(
                calc_type, base_path, context.compound_name,
                context.is_input, context.stress_amounts
            )

            if paths:
                raw_paths[calc_name] = paths

        # Organize paths into structured format
        return self.path_organizer.organize_paths(raw_paths, context)

    def create_directories(self, context: PathBuildingContext) -> List[str]:
        """Create project directories."""
        self.directory_manager = DirectoryManager(context.project_dir)
        return self.directory_manager.create_project_directories(context)


def get_project_directory(compound_name: str) -> str:
    """
    Get the project directory for the given compound.

    Args:
        compound_name (str): Name of the compound.

    Returns:
        str: The absolute path to the project directory.
    """
    script_root_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".."))  # The root directory of the program
    user_id = os.getenv("COFFEE")
    user_path = os.path.join(script_root_dir, "..", user_id) if user_id else ".."
    root_dir = os.path.abspath(user_path)  # The root directory of the project
    return os.path.join(root_dir, compound_name)  # The calculation directory


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
        is_pdos: bool = False,
        skip_soc: bool = False,
        skip_normal: bool = False
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
        skip_soc (bool): Whether to skip SOC calculations.
        skip_normal (bool): Whether to skip normal (non-SOC) calculations.

    Returns:
        ProjectSetup: An object containing the initialized project setup details.

    Raises:
        ProjectInitializationError: If parsing the compound name fails.
    """
    print('\n')
    print_header("Project Initialization")

    # Validate skip flags
    if skip_soc and skip_normal:
        raise ProjectInitializationError("Both skip_soc and skip_normal cannot be True simultaneously.")

    config = load_project_config(config_file, config_type)

    # Detect if SOC directories are available in config
    soc_available = has_soc_directories(config.directory_structure)

    # Determine skip_soc flag
    final_skip_soc = skip_soc

    if not soc_available:
        if not skip_normal:
            # No SOC directories in config, automatically skip SOC
            final_skip_soc = True
            print_info("No SOC directories found in configuration. SOC calculations will be skipped.")
        else:
            # We cannot proceed with skipping normal calculations if SOC directories are not available
            raise ProjectInitializationError(
                "Cannot skip normal calculations when SOC directories are not available in the configuration.")

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

    context = PathBuildingContext(
        project_dir=project_dir,
        compound_name=compound_name,
        config=config,
        is_input=is_input,
        include_stress=include_stress,
        stress_amounts=stress_amounts,
        skip_soc=skip_soc,
        skip_normal=skip_normal
    )

    path_manager = PathManager()

    if is_input:
        # Create the required calculation directories
        calculation_dirs = path_manager.create_directories(context)
        paths = path_manager.build_file_paths(context)

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
            ) if not skip_soc else None,
            input_paths=paths,
            poscar_file=os.path.abspath(poscar_file),
            skip_soc=final_skip_soc,
            skip_normal=skip_normal
        )

    else:
        # For output/analysis, return the project setup details
        if final_skip_soc:
            paths = path_manager.build_file_paths(context)
        else:
            paths = path_manager.build_file_paths(context)

            # Update final_skip_soc if stress calculations force SOC to be skipped
            if context.include_stress:
                final_skip_soc = True

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
            ) if not final_skip_soc else None,
            output_paths=paths,
            skip_soc=final_skip_soc,
            skip_normal=skip_normal
        )


# Test to ensure the module works as expected
if __name__ == "__main__":
    """
    Main entry point for testing the module.
    
    Validates the functionality of the `prepare_paths` function and checks if all required files exist.
    """
    def validate_compound_name(value):
        if os.path.sep in value or os.path.altsep and os.path.altsep in value:
            raise argparse.ArgumentTypeError(f"'{value}' is not a valid compound name as it contains path separators.")
        return value

    # Create the parser
    parser = argparse.ArgumentParser(description="Tests the path handler module.")

    # Add arguments
    parser.add_argument(
        "compound_name",
        type=validate_compound_name,
        help="Name of the compound (e.g., 'GaAs', 'SiO2')."
    )
    parser.add_argument(
        "poscar_file",
        type=str,
        nargs='?',
        help="Path to the POSCAR file (required for input file generation)."
    )

    parser.add_argument(
        "--initialize-input",
        action="store_true",
        help="Initialize the project for input files."
    )

    parser.add_argument(
        "--project-config",
        type=str,
        help="Path to a custom JSON project configuration file."
    )

    parser.add_argument(
        "--config-type",
        type=str,
        default="default",
        choices=["default", "bands", "pdos", "wannier"],
        help="Type of configuration to use (default: 'default')."
    )

    args = parser.parse_args(argv[1:])
    is_input = args.initialize_input
    try:
        # Initialize and prepare project
        project = initialize_project(args.compound_name,
                                     args.project_config,
                                     args.config_type,
                                     args.poscar_file if is_input else None,
                                     is_input=is_input)

        print_header("Project Initialization Summary")
        print('\n')
        # Creating a table for project information
        info_table = Table(show_header=True, box=box.ROUNDED, title="Project Information", show_lines=True)
        info_table.add_column("Property", style=custom_theme.styles["info"])
        info_table.add_column("Value", style="green")

        info_table.add_row("Compound name", project.compound_name)
        info_table.add_row("Project directory", project.project_dir)
        info_table.add_row("Include stress", str(project.include_stress))
        if project.include_stress:
            info_table.add_row("Stress amounts", ", ".join(project.stress_amounts))
        info_table.add_row("Pseudo dir", project.pseudo_dir)
        info_table.add_row("Rel pseudo dir", project.rel_pseudo_dir)
        info_table.add_row("Elements", ", ".join(project.compound_data.element_names))
        info_table.add_row("Atomic labels", ", ".join(project.compound_data.atomic_labels))

        console.print(info_table, '\n')

        # Display paths in a separate table
        paths_table = Table(title="File Paths", show_header=True, show_lines=True)
        paths_table.add_column("Type", style="cyan")
        paths_table.add_column("Paths", style="green", overflow="fold")

        paths_dict = project.input_paths if is_input else project.output_paths
        for path_type, paths in paths_dict.items():
            paths_table.add_row(path_type, "\n".join(paths))

        console.print(paths_table)

    except ProjectInitializationError as e:
        print_error(f"Error during project initialization: {str(e)}")
        exit(1)

    except Exception as e:
        print_error(f"Unexpected Error: {str(e)}")
        exit(1)
