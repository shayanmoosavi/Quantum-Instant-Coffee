""" Path management module for organizing and creating project directories and file paths.

Classes:
    - DirectoryManager: Manages directory creation and validation.
    - StructuredPathOrganizer: Organizes paths into a structured format expected by the application.
    - PathManager: Main class that coordinates all path-related operations.
"""
import os
from typing import List, Dict

from .builders import FilePatternBuilder, CalculationPathBuilder
from .exceptions import ProjectInitializationError
from .models import PathBuildingContext, CalculationType
from .organizer import StructuredPathOrganizer
from ui.ui_helpers import print_error


class DirectoryManager:
    """
    Manages directory creation and validation.

    Attributes:
        project_dir (str): The root directory of the project.
    """

    def __init__(self, project_dir: str):
        """
        Initializes the DirectoryManager with the project directory.

        Args:
            project_dir (str): The root directory of the project.
        """
        self.project_dir = project_dir

    def create_project_directories(self, context: PathBuildingContext) -> List[str]:
        """
        Creates all required directories for the project based on the provided context.

        Args:
            context (PathBuildingContext): The context containing project configuration and settings.

        Returns:
            List[str]: A list of absolute paths to the created directories.

        Raises:
            ProjectInitializationError: If an invalid calculation type is found in the directory structure.
        """
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


class DynamicPathResolver:
    """
    Resolves paths dynamically during data processing with existence validation
    and user prompts for missing files.
    """

    def __init__(self, context: PathBuildingContext, soc_handler):
        """
        Initialize the dynamic path resolver.

        Args:
            context: PathBuildingContext with project configuration
            soc_handler: SpinOrbitHandler instance for managing skip logic
        """
        self.context = context
        self.soc_handler = soc_handler
        self.pattern_builder = FilePatternBuilder(context.config.file_patterns.output)
        self.calc_path_builder = CalculationPathBuilder(self.pattern_builder)
        self._path_cache = {}

    def get_calculation_paths(self, calc_type: CalculationType,
                              validate_existence: bool = True) -> Dict[str, List[str]]:
        """
        Get paths for a specific calculation type with optional existence validation.

        Args:
            calc_type: The calculation type to get paths for
            validate_existence: Whether to check if files exist and prompt user

        Returns:
            Dict of file types to path lists, or empty dict if skipped
        """
        # Check if this calculation type should be skipped
        flag = "_soc" if calc_type.is_soc else ""

        if self.soc_handler.should_skip(flag):
            return {}

        # Use cache if available
        cache_key = calc_type.value
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]

        # Build paths for this calculation type
        calc_name = calc_type.value
        if calc_name not in self.context.config.directory_structure:
            return {}

        dir_path = self.context.config.directory_structure[calc_name]
        base_path = os.path.join(self.context.project_dir, dir_path)

        try:
            paths = self.calc_path_builder.build_paths_for_calculation(
                calc_type, base_path, self.context.compound_name,
                self.context.is_input, self.context.stress_amounts
            )

            if validate_existence:
                paths = self._validate_and_prompt(paths, flag)

            # Cache the result
            self._path_cache[cache_key] = paths
            return paths

        except Exception as e:
            print_error(f"Error building paths for {calc_type.value}: {e}")
            return {}

    def _validate_and_prompt(self, paths: Dict[str, List[str]], flag: str) -> Dict[str, List[str]]:
        """
        Validate file existence and prompt user if files are missing.

        Args:
            paths: Dictionary of file types to path lists
            flag: SOC flag ("_soc" or "")

        Returns:
            Original paths if valid, empty dict if user chooses to skip
        """
        # Check if any required files exist
        files_exist = False
        missing_files = []

        for _, file_paths in paths.items():
            for file_path in file_paths:
                if os.path.exists(file_path):
                    files_exist = True
                else:
                    missing_files.append(file_path)

        if files_exist:
            # At least some files exist, mark as found and return paths
            self.soc_handler.mark_found(flag)
            return paths

        # No files found - handle the error through SOC handler
        should_skip = self.soc_handler.handle_error(flag)

        if should_skip:
            return {}
        else:
            # User chose not to skip, return empty paths (or could raise exception)
            return {}

    def get_organized_paths(self, calc_types: List[CalculationType]) -> Dict[str, List[str]]:
        """
        Get organized paths for multiple calculation types.

        Args:
            calc_types: List of calculation types to process

        Returns:
            Organized paths dictionary suitable for data processing
        """
        raw_paths = {}

        for calc_type in calc_types:
            paths = self.get_calculation_paths(calc_type, validate_existence=True)
            if paths:  # Only include if not skipped
                raw_paths[calc_type.value] = paths

        # Use the existing organizer to structure the paths
        organizer = StructuredPathOrganizer()
        return organizer.organize_paths(raw_paths, self.context)


class PathManager:
    """
    Main class that coordinates all path-related operations.

    Attributes:
        pattern_builder (FilePatternBuilder): Builder for file patterns.
        calc_path_builder (CalculationPathBuilder): Builder for calculation paths.
        directory_manager (DirectoryManager): Manager for project directories.
        path_organizer (StructuredPathOrganizer): Organizer for structured paths.
    """

    def __init__(self):
        """
        Initializes the PathManager with default builders and organizers.
        """
        self.pattern_builder = None
        self.calc_path_builder = None
        self.directory_manager = None
        self.path_organizer = StructuredPathOrganizer()

    def build_file_paths(self, context: PathBuildingContext) -> Dict[str, List[str]]:
        """
        Builds file paths based on the provided context.

        Args:
            context (PathBuildingContext): The context containing project configuration and settings.

        Returns:
            Dict[str, List[str]]: Structured file paths grouped by keys.

        Raises:
            ProjectInitializationError: If an invalid calculation type is found in the directory structure.
        """
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
        """
        Creates project directories based on the provided context.

        Args:
            context (PathBuildingContext): The context containing project configuration and settings.

        Returns:
            List[str]: A list of absolute paths to the created directories.
        """
        self.directory_manager = DirectoryManager(context.project_dir)
        return self.directory_manager.create_project_directories(context)

    @staticmethod
    def create_dynamic_resolver(context: PathBuildingContext,
                                soc_handler) -> DynamicPathResolver:
        """
        Create a dynamic path resolver for runtime path resolution.

        Args:
            context: PathBuildingContext with project configuration
            soc_handler: SpinOrbitHandler instance

        Returns:
            DynamicPathResolver instance
        """
        return DynamicPathResolver(context, soc_handler)
