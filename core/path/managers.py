import os
from typing import List, Dict

from core.path.builders import FilePatternBuilder, CalculationPathBuilder
from core.path.exceptions import ProjectInitializationError
from core.path.models import PathBuildingContext, CalculationType


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
