import argparse
import os
from sys import argv

from core.path import initialize_project
from core.path.exceptions import ProjectInitializationError
from ui.ui_helpers import *

if __name__ == "__main__":
    """
    Main entry point for testing the project initialization.
    
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
