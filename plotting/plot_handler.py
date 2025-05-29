"""Module for handling the plotting of processed data from DFT and Wannier calculations.

This module provides classes and functions for visualizing band structure data,
including regular band structures, orbital-projected band structures, and
comparisons between Wannier and DFT band structures.

Classes:
    ProjectionDataProcessor: Processes atomic projection data for band structure plotting.

Functions:
    plot_band_structure: Plot band structure from processed data.
    plot_wannier_comparison: Plot Wannier and DFT band structure comparison.
    plot_pdos: Plot projected density of states (PDOS) data.
"""
import os
from sys import argv
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
from rich.table import Table

from core.config_handler import BandsPlotConfig, DOSPlotConfig
from data.data_processor import process_band_data, process_comparison_data, process_pdos_data, AtomicProjectionProcessor
from data.data_collector import prepare_bands_info, prepare_wannier_info, prepare_pdos_info
from data.models import ProjectSetup
from core.project_setup import initialize_project
from plotting.plotters import BandPlotter, WannierComparePlotter, DOSPlotter
from ui.display_plot_info import display_band_plot_info, display_wannier_plot_info, display_pdos_plot_info
from ui.ui_helpers import print_header, console, print_success, prompt_input
from ui.print_thanks import print_animated_ascii


class ProjectionDataProcessor:
    """Processes atomic projection data for band structure or DOS plotting.

    This class handles the processing of atomic projection weights and organizing
    them by element and orbital type for visualization.

    Args:
        weights_info_list (list): List of dictionaries containing projection weights
        unique_elements_list (list): List of unique chemical elements
        is_pdos (bool): Flag indicating whether to process PDOS data
    """

    def __init__(self,
                 config: BandsPlotConfig | DOSPlotConfig,
                 unique_elements_list: List[str],
                 *,
                 is_pdos: bool = False,
                 weights_info_list: List[Dict] = None,
                 pdos_info_list: List[Dict] = None,
                 dos_data_list: List[Dict] = None
                 ) -> None:
        """Initialize the ProjectionDataProcessor.

        Args:
            config (BandsPlotConfig | DOSPlotConfig): Configuration object with plot parameters
            unique_elements_list (list): List of unique chemical elements
            is_pdos (bool): Flag indicating whether to process PDOS data
            weights_info_list (list): List of dictionaries containing projection weights
            pdos_info_list (list): List of dictionaries containing PDOS projection data
            dos_data_list (list): List of dictionaries containing DOS data
        """
        if not is_pdos:
            self.config = config or BandsPlotConfig.get_default_config()
            self.weights_info_list = weights_info_list
            self.elements_list = unique_elements_list
            self.is_pdos = is_pdos
        else:
            self.config = config or DOSPlotConfig()
            self.elements_list = unique_elements_list
            self.pdos_info_list = pdos_info_list
            self.is_pdos = is_pdos
            self.dos_data_list = dos_data_list

    def process_projections(self) -> List[Dict]:
        """Process projection data for all elements.

        Returns:
            list: List of processed projection data dictionaries
        """
        if not self.is_pdos:
            projection_info_list = []

            for weights_info in self.weights_info_list:
                projection_info = {}

                for i, element in enumerate(self.elements_list):
                    projection_info[element] = self._process_element_projections(
                        element, i, weights_info=weights_info)

                projection_info_list.append(projection_info)

            return projection_info_list
        else:

            projection_info_list = []

            for dos_data in self.dos_data_list:
                projection_info = {}

                for i, element in enumerate(self.elements_list):
                    projection_info[element] = self._process_element_projections(
                        element, i, dos_data=dos_data)

                projection_info_list.append(projection_info)
            return projection_info_list

    def _process_element_projections(self,
                                     element: str,
                                     index: int,
                                     *,
                                     weights_info: Dict[str, np.ndarray] = None,
                                     dos_data: Dict[str, Dict[str, np.ndarray]] = None) -> Dict:
        """Process projection data for a single element.

        Args:
            element (str): Chemical element symbol
            index (int): Element index
            weights_info (dict): Dictionary containing projection weights
            dos_data (dict): Dictionary containing DOS data

        Returns:
            dict: Processed projection data for the element
        """
        if not self.is_pdos:
            orbitals = []
            colors = []
            weights = []

            for orbital, color in self.config.orbital_colors.items():
                projection = f"{element}-{orbital}"

                # Check if this projection exists in the weights_info
                if projection in weights_info:
                    orbitals.append(orbital)
                    colors.append(color)
                    weights.append(weights_info[projection])

            return {
                "index": index + 1,
                "projected_orbitals": orbitals,
                "plot_colors": colors,
                "orbital_weights": weights
            }

        else:
            orbitals = []
            colors = []
            energies = []
            pdos = []

            for orbital, color in self.config.orbital_colors.items():
                projection = f"{element}-{orbital}"

                # Check if this projection exists in the weights_info
                if projection in dos_data:
                    orbitals.append(orbital)
                    colors.append(color)
                    energies.append(dos_data[projection]["energy"])
                    pdos.append(dos_data[projection]["dos"])

            return {
                "index": index + 1,
                "projected_orbitals": orbitals,
                "plot_colors": colors,
                "energies": energies,
                "pdos": pdos
            }

    @staticmethod
    def combine_similar_orbitals(weights_info: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Combine orbital projections with the same contribution (like px and py).

        Args:
            weights_info (dict): Dictionary mapping projections to weights

        Returns:
            dict: Dictionary with combined orbital projections
        """
        combined_weights = {}

        # Defining orbital combinations
        orbital_combinations = {
            "px+py": ["px", "py"],
            "dxz+dyz": ["dxz", "dyz"],
            "dx2y2+dxy": ["dx2y2", "dxy"]
        }

        # Processing all projections
        for projection, weight in weights_info.items():
            atom, orbital = projection.split("-")

            # Checking if this orbital needs to be combined
            combined = False
            for combined_name, orbitals in orbital_combinations.items():
                if orbital in orbitals:
                    combined_key = f"{atom}-{combined_name}"
                    if combined_key not in combined_weights:
                        combined_weights[combined_key] = weight
                    else:
                        # Adding weights for combined orbitals
                        combined_weights[combined_key] += weight
                    combined = True
                    break

            # If not combined, keep as is
            if not combined:
                combined_weights[projection] = weight

        return combined_weights


def plot_band_structure(project: ProjectSetup,
                        plot_config: BandsPlotConfig = BandsPlotConfig.get_default_config(),
                        save_fig: bool = True,
                        test_module: bool = False) -> None:
    """
    Plot band structure from processed data.

    Args:
        project (ProjectSetup): Project configuration and data container
        plot_config (BandsPlotConfig, optional): Plotting configuration. Defaults to BandsPlotConfig().
        save_fig (bool, optional): Whether to save the plots to files. Defaults to True.
        test_module (bool, optional): If True, prints debug information instead of plotting. Defaults to False.
    """
    print_header("Processing Band Structure Data")

    # Initializing objects for plotting and processing projection data
    plotter = BandPlotter(plot_config)
    processor = ProjectionDataProcessor(
        plot_config,
        project.band_data.unique_elements,
        weights_info_list=project.band_data.atomic_projection_weights
    )

    with console.status("Processing projection data..."):
        # Process projection data into a structured format
        projection_info_list = processor.process_projections()

    # Extracting configuration values
    compound_name = project.compound_name
    spin_orbit_flags = project.band_info.spin_orbit_flags if project.band_info.spin_orbit_flags else [False] * len(
        project.band_data.energy)
    stress_amount_list = (["1"] + project.stress_amounts) if project.include_stress else ["1"] * len(
        project.band_data.energy)
    total_plots = len(spin_orbit_flags)

    if test_module:
        # Debug mode: Printing projection information for verification
        for projection_info, spin_orbit_flag, stress_amount in zip(
                projection_info_list,
                project.band_info.spin_orbit_flags or [False] * len(project.band_data.energy),
                (["1"] + project.stress_amounts) if project.include_stress else ["1"] * len(project.band_data.energy)
        ):
            print('\n')
            display_band_plot_info(projection_info,
                                   spin_orbit_flag,
                                   project.include_stress,
                                   stress_amount)
    else:
        # Plotting mode: Generating plots for each dataset
        for i, (projection_data, k_points, energy, k_points_proj, energy_proj,
                number_of_bands, spin_orbit, stress_amount) in enumerate(zip(
            projection_info_list,
            project.band_data.k_points,
            project.band_data.energy,
            project.band_data.k_points_proj,
            project.band_data.energy_proj,
            project.band_info.number_of_bands,
            spin_orbit_flags,
            stress_amount_list), 1):

            console.rule(f"Processing dataset {i} of {total_plots}")

            if save_fig:
                # Generating file name for saving the plot
                if spin_orbit:
                    file_name = f"{compound_name}_projbands_soc.png"
                elif stress_amount != "1":
                    file_name = f"{compound_name}_projbands{stress_amount}.png"
                else:
                    file_name = f"{compound_name}_projbands.png"

                save_path = os.path.join(project.project_dir, file_name)

                with console.status("Creating band structure plot..."):
                    # Creating and saveing the plot
                    plotter.create_band_structure_plot(
                        compound_name,
                        k_points,
                        energy,
                        k_points_proj,
                        energy_proj,
                        projection_data,
                        number_of_bands,
                        spin_orbit,
                        stress_amount,
                        save_path
                    )
                    print_success(f"Created: `{file_name}`")

            else:
                with console.status("Creating band structure plot..."):
                    # Creating and displaying the plot without saving
                    plotter.create_band_structure_plot(
                        compound_name,
                        k_points,
                        energy,
                        k_points_proj,
                        energy_proj,
                        projection_data,
                        number_of_bands,
                        spin_orbit,
                        stress_amount
                    )
                plt.show()
                print_success("Plot displayed successfully.")

        print_animated_ascii("ascii-art.txt")
        console.print("\nThanks for using Quantum Instant Coffee :)", style="bold cyan")


def plot_wannier_comparison(project: ProjectSetup,
                            plot_config: BandsPlotConfig = BandsPlotConfig.get_default_config(),
                            save_fig: bool = True,
                            test_module: bool = False) -> None:
    """Plot Wannier and DFT band structure comparison.

    Args:
        project (ProjectSetup): Project configuration and data container
        plot_config (BandsPlotConfig, optional): Plotting configuration. Defaults to BandsPlotConfig().
        save_fig (bool, optional): Whether to save the plots to files. Defaults to True.
        test_module (bool, optional): If True, prints debug information instead of plotting. Defaults to False.
    """
    print_header("Processing Wannier Comparison Data")

    plotter = WannierComparePlotter(plot_config)
    comparison_data = project.wannier_setup.comparison_data
    spin_orbit_flags = ["_soc"] if project.wannier_setup.skip_normal else ["", "_soc"]
    total_plots = len(spin_orbit_flags)

    if test_module:

        for i, (fermi_energy, alat, flag) in enumerate(zip(
                project.wannier_setup.fermi_energies,
                project.wannier_setup.alat_parameters,
                spin_orbit_flags
        ), 1):
            console.rule(f"Processing dataset {i} of {total_plots}")
            display_wannier_plot_info(fermi_energy, alat, flag)

    else:
        for i, (k_points_dft, dft_energies, k_points_wannier, wannier_energies, flag) in enumerate(zip(
                comparison_data["k_points_dft"],
                comparison_data["dft_energies"],
                comparison_data["k_points_wannier"],
                comparison_data["wannier_energies"],
                spin_orbit_flags
        ), 1):

            console.rule(f"Processing dataset {i} of {total_plots}")

            if save_fig:

                file_name = f"{project.compound_name}_comparison{flag}.png"
                save_path = os.path.join(
                    project.project_dir,
                    file_name
                )

                with console.status("Creating Wannier comparison plot..."):
                    plotter.init_plot(
                        project.compound_name,
                        project.wannier_setup.skip_normal,
                        flag
                    )
                    plotter.plot_comparison(
                        k_points_dft,
                        dft_energies,
                        k_points_wannier,
                        wannier_energies,
                        save_path
                    )
                print_success(f"Created: `{file_name}`")

            else:
                with console.status("Creating Wannier comparison plot..."):
                    plotter.init_plot(
                        project.compound_name,
                        project.wannier_setup.skip_normal,
                        flag
                    )
                    plotter.plot_comparison(
                        k_points_dft,
                        dft_energies,
                        k_points_wannier,
                        wannier_energies
                    )
                plt.show()
                print_success("Plot displayed successfully.")

        print_animated_ascii("ascii-art.txt")
        console.print("\nThanks for using Quantum Instant Coffee :)", style="bold cyan")


def plot_pdos(project: ProjectSetup,
              plot_config: DOSPlotConfig = DOSPlotConfig.get_default_config(),
              save_fig: bool = False,
              test_module: bool = False) -> None:
    """Plot projected DOS.

    Args:
        project (ProjectSetup): Project configuration and data container
        plot_config (PDOSPlotConfig, optional): Plotting configuration. Defaults to PDOSPlotConfig().
        save_fig (bool, optional): Whether to save the plots to files. Defaults to False.
        test_module (bool, optional): If True, prints debug information instead of plotting. Defaults to False.
    """
    print_header("Processing PDOS Data")

    compound_name = project.compound_name
    spin_orbit_flags = ["", "_soc"]
    projection_processor = AtomicProjectionProcessor(list(project.dos_setup.atomic_states_info[0].keys()))
    unique_elements_list = projection_processor.get_unique_elements()
    total_plots = len(spin_orbit_flags)

    with console.status("Processing projection data..."):
        projection_data_processor = ProjectionDataProcessor(plot_config,
                                                            unique_elements_list,
                                                            is_pdos=True,
                                                            pdos_info_list=project.dos_setup.atomic_states_info,
                                                            dos_data_list=project.dos_setup.dos_data
                                                            )

        projection_data_list = projection_data_processor.process_projections()

    if test_module:

        for i, (projection_data, flag) in enumerate(
                zip(projection_data_list, spin_orbit_flags), 1):
            console.rule(f"Processing dataset {i} of {total_plots}")
            print('\n')
            display_pdos_plot_info(unique_elements_list, projection_data)

    else:

        plotter = DOSPlotter(plot_config)

        for i, (projection_data, flag) in enumerate(
                zip(projection_data_list, spin_orbit_flags), 1):

            console.rule(f"Processing dataset {i} of {total_plots}")

            # Get total DOS from first element's energy values
            energy = projection_data[unique_elements_list[0]]["energies"][0]
            pdos_total = np.zeros_like(energy)

            # Sum up all orbital contributions for total DOS
            with console.status("Calculating total DOS"):
                for element_data in projection_data.values():
                    for pdos in element_data["pdos"]:
                        pdos_total += pdos
            print_success("Total DOS calculated successfully.")

            if save_fig:
                file_name = f"{compound_name}_pdos{flag}.png"
                save_path = os.path.join(
                    project.project_dir,
                    file_name
                )

                # Create and save the plot
                with console.status("Creating PDOS plot..."):
                    plotter.create_pdos_plot(
                        compound_name,
                        energy,
                        pdos_total,
                        projection_data,
                        flag == "_soc",
                        save_path
                    )
                print_success(f"Created: `{file_name}`")

            else:
                # Creating and displaying the plot
                with console.status("Creating PDOS plot..."):
                    plotter.create_pdos_plot(
                        compound_name,
                        energy,
                        pdos_total,
                        projection_data,
                        flag == "_soc"
                    )
                    plt.show()
                print_success("Plot displayed successfully.")

        print_animated_ascii("ascii-art.txt")
        console.print("\nThanks for using Quantum Instant Coffee :)", style="bold cyan")


if __name__ == "__main__":
    """
    Main entry point for the script. Prepares configuration, processes data, and plots band structures.

    Steps:
        1. Determine if the script is being run for input generation or output processing.
        2. Prompt the user to check if Wannier comparison is being tested.
        3. Initialize the project with the appropriate configuration.
        4. Prepare Wannier or DFT information based on the user's input.
        5. Process the comparison or band data for plotting.
        6. Generate and display the appropriate plots (Wannier comparison or band structure).
    """
    os.chdir("..")

    # Create initialization options table
    options_table = Table(title="Available Initialization Types")
    options_table.add_column("Type", style="cyan")
    options_table.add_column("Description", style="green")
    options_table.add_row("wannier", "Prepare Wannier bands comparison setup")
    options_table.add_row("bands", "Extract band structure information")
    options_table.add_row("pdos", "Process projected density of states")
    console.print(options_table)

    # Check if the script is being run for input generation (3 arguments passed)
    is_input = len(argv) == 3

    response = prompt_input(
        "Enter the initialization type you want to test for (wannier, bands, pdos): ").strip().lower()

    match response:
        case "wannier":
            project = initialize_project(argv, is_input, is_wannier=True)
            prepare_wannier_info(project)
            process_comparison_data(project)

            plot_config = BandsPlotConfig.get_default_config()
            plot_wannier_comparison(project, plot_config, save_fig=False, test_module=True)

        case "bands":
            project = initialize_project(argv, is_input)
            prepare_bands_info(project)
            process_band_data(project)

            plot_config = BandsPlotConfig.get_default_config()
            plot_band_structure(project, plot_config, save_fig=False, test_module=True)

        case "pdos":
            project = initialize_project(argv, is_input, is_pdos=True)
            prepare_pdos_info(project)
            process_pdos_data(project)

            plot_config = DOSPlotConfig.get_default_config()
            plot_pdos(project, plot_config, save_fig=False, test_module=False)

        case _:
            raise ValueError("Invalid initialization type! Valid choices are: wannier, bands, pdos")
