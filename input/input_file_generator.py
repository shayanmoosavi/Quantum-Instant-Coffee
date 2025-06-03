""" High-level manager for generating and writing input files for Quantum ESPRESSO and Wannier90 calculations.

This module provides functionality to manage the generation and writing of input files required for Quantum ESPRESSO
and Wannier90 calculations. It includes classes and methods for initializing project contexts, generating input files,
and writing them to disk.

Classes:
    InputFileManager: Manages the generation and writing of input files for a given project.
"""
import argparse
import os
from sys import argv

from core.input_handler import get_pseudopotential_files
from core.path import initialize_project
from data.fetch_atomic_info import get_atomic_weights
from data.models import ProjectSetup
from input.generators.factory import InputGeneratorFactory, GenerationContext
from input.generators.sections import InputGenerationError
from ui.print_thanks import print_animated_ascii
from ui.ui_helpers import *
from utils.file_parser import get_poscar_data


class InputFileManager:
    """High-level manager for input file generation and writing."""

    def __init__(self, project: ProjectSetup):
        """
        Initializes the InputFileManager with the given project setup.

        Args:
            project (ProjectSetup): The project setup containing compound data, paths, and configuration.
        """
        self.project = project
        self.factory = InputGeneratorFactory()
        self._context = None

    def initialize_context(self) -> GenerationContext:
        """
        Initializes the generation context with all required data.

        This method retrieves atomic weights, POSCAR data, and pseudopotential files, and sets up the context
        for input file generation.

        Returns:
            GenerationContext: The initialized context containing project data and atomic information.
        """
        print_info("Fetching atomic weights and POSCAR data...")
        with console.status("Retrieving atomic weights and POSCAR data"):
            atomic_weights = get_atomic_weights(self.project.compound_data.element_names)
            lattice_vectors, atomic_positions = get_poscar_data(self.project.poscar_file)

        print_info("Fetching the Pseudopotentials...")
        pseudo_list, rel_pseudo_list = get_pseudopotential_files(
            self.project.compound_data.element_names,
            self.project.pseudo_dir,
            relativistic=True,
            rel_pseudo_path=self.project.rel_pseudo_dir
        )
        print_info("Pseudopotentials fetched successfully.")

        self._context = GenerationContext(
            project=self.project,
            atomic_weights=atomic_weights,
            pseudo_list=pseudo_list,
            rel_pseudo_list=rel_pseudo_list,
            atomic_positions=atomic_positions,
            lattice_vectors=lattice_vectors
        )

        return self._context

    def generate_input_file(self, input_type: str, relativistic: bool = False, **kwargs) -> str:
        """
        Generates a single input file for the specified type.

        Args:
            input_type (str): The type of input file to generate (e.g., 'nscf', 'pdos').
            relativistic (bool): Whether to generate input files for relativistic calculations.
            **kwargs: Additional parameters for input file generation.

        Returns:
            str: The generated input file content.
        """
        if self._context is None:
            self.initialize_context()

        # Update context for relativistic calculation
        context = GenerationContext(
            project=self._context.project,
            atomic_weights=self._context.atomic_weights,
            pseudo_list=self._context.pseudo_list,
            rel_pseudo_list=self._context.rel_pseudo_list,
            atomic_positions=self._context.atomic_positions,
            lattice_vectors=self._context.lattice_vectors,
            relativistic=relativistic
        )

        generator = self.factory.create_generator(input_type)
        return generator.generate(context, **kwargs)

    def write_all_input_files(self, skip_soc: bool = False) -> None:
        """
        Writes all input files for the project.

        This method generates and writes input files for all specified types in the project configuration.
        It supports both SOC and non-SOC versions, and handles errors during generation and writing.

        Args:
            skip_soc (bool): Whether to skip generating SOC input files.
        """
        if self._context is None:
            self.initialize_context()

        print_info("Starting input file generation...\n")
        print_header("Input File Generation")

        generated_files = []

        print_info("Generating input files...")
        for key, paths in self.project.input_paths.items():
            input_type = key.replace("_paths", "").replace("_input", "")

            try:
                generator = self.factory.create_generator(input_type)
            except InputGenerationError:
                continue  # Skip unknown input types

            if not self.project.include_stress:
                # Generate both normal and SOC versions
                for path, relativistic in zip(paths, [False, True]):
                    file_name = os.path.basename(path)

                    if "_soc" in file_name and skip_soc:
                        print_info(f"Skipping SOC file generation for {file_name}")
                        continue

                    context = GenerationContext(
                        project=self._context.project,
                        atomic_weights=self._context.atomic_weights,
                        pseudo_list=self._context.pseudo_list,
                        rel_pseudo_list=self._context.rel_pseudo_list,
                        atomic_positions=self._context.atomic_positions,
                        lattice_vectors=self._context.lattice_vectors,
                        relativistic=relativistic
                    )

                    try:
                        content = generator.generate(context)
                        generated_files.append((file_name, path, content))
                    except Exception as e:
                        print_error(f"Error generating {file_name}: {str(e)}")
                        continue
            else:
                # Generate only normal version
                for path in paths:
                    file_name = os.path.basename(path)

                    context = GenerationContext(
                        project=self._context.project,
                        atomic_weights=self._context.atomic_weights,
                        pseudo_list=self._context.pseudo_list,
                        rel_pseudo_list=self._context.rel_pseudo_list,
                        atomic_positions=self._context.atomic_positions,
                        lattice_vectors=self._context.lattice_vectors,
                        relativistic=False
                    )

                    try:
                        content = generator.generate(context)
                        generated_files.append((file_name, path, content))
                    except Exception as e:
                        print_error(f"Error generating {file_name}: {str(e)}")
                        continue

        print_success("\nInput files have been generated successfully.\n")
        print_header("Writing Input Files")

        for file_name, path, content in progress_track(generated_files, description="Writing input files"):
            try:
                with open(path, "w") as f:
                    f.write(content)
                print_success(f"Wrote {file_name} at:\n    {path}")
            except Exception as e:
                print_error(f"Error writing {file_name}: {str(e)}")

        print_success("All input files have been written successfully.")
        print_animated_ascii("ascii-art.txt")
        console.print("\nThanks for using Quantum Instant Coffee :)", style="bold cyan")


if __name__ == "__main__":
    """
    Main entry point for the script.

    This block initializes the project, retrieves necessary data, and generates
    the NSCF input file for Quantum ESPRESSO calculations. It performs the following steps:
    1. Determines if the script is called for input file generation.
    2. Initializes the project setup using command-line arguments.
    3. Retrieves pseudopotential files for the specified elements.
    4. Fetches atomic weights and POSCAR data (lattice vectors and atomic positions).
    5. Generates the NSCF input file using the provided data and configuration.
    6. Prints the generated NSCF input file content.
    """
    # Create the parser
    parser = argparse.ArgumentParser(description="Writes input files for Quantum ESPRESSO and Wannier90 calculations.")

    # Add arguments
    parser.add_argument(
        "compound_name",
        type=str,
        help="Name of the compound (e.g., 'GaAs', 'SiO2')."
    )
    parser.add_argument(
        "poscar_file",
        type=str,
        help="Path to the POSCAR file."
    )

    # Parse the arguments
    args = parser.parse_args(argv[1:])
    compound_name, poscar_file = args.compound_name, args.poscar_file

    os.chdir("..")

    project = initialize_project(compound_name, poscar_file=poscar_file, is_input=True)

    manager = InputFileManager(project)

    try:
        nscf_input = manager.generate_input_file("nscf", relativistic=True)
        print_info(nscf_input)
    except Exception as e:
        print_error(f"Error generating NSCF input: {str(e)}")