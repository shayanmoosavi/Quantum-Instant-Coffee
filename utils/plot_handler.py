"""Module for handling the plotting of processed data from DFT and Wannier calculations.

This module provides classes and functions for visualizing band structure data,
including regular band structures, orbital-projected band structures, and
comparisons between Wannier and DFT band structures.

Classes:
    PlotConfig: Configuration class containing constants for plot styling and parameters.
    CompoundNameFormatter: Formats chemical compound names into LaTeX representation.
    BandPlotter: Class for plotting band structure diagrams.
    WannierComparePlotter: Class for plotting Wannier and DFT band structure comparison plots.
    ProjectionDataProcessor: Processes atomic projection data for band structure plotting.

Functions:
    plot_band_structure: Plot band structure from processed data.
    plot_wannier_comparison: Plot Wannier and DFT band structure comparison.
"""

import re
import os
from sys import argv
from typing import Dict, List
import matplotlib.axes
import matplotlib.collections
import matplotlib.pyplot as plt
import numpy as np

from data.data_processor import process_band_data, process_comparison_data, process_pdos_data, AtomicProjectionProcessor
from data.dft_info_extractor import prepare_bands_info, prepare_wannier_info, prepare_pdos_info
from data.models import ProjectSetup
from core.project_setup import initialize_project


class BandsPlotConfig:
    """Configuration class containing constants for plot styling and parameters.

    Attributes:
        HIGH_SYMMETRY_K_POINTS (list): K-point coordinates for high symmetry points in k-space
        K_LABELS (list): LaTeX formatted labels for high symmetry k-points
        ORBITAL_COLORS (dict): Color codes for different orbital types
        FIGURE_HEIGHT (int): Default figure height in inches
        FIGURE_WIDTH (int): Default figure width in inches
        ENERGY_LIMITS (tuple): Y-axis energy range in eV
    """
    HIGH_SYMMETRY_K_POINTS = [0.0000, 0.5774, 0.9107, 1.5774]
    K_LABELS = [r"$\Gamma$", r"$M$", r"$K$", r"$\Gamma$"]
    ORBITAL_COLORS = {
        "s": "#FF00ED",
        "p": "#0BF317",
        "d": "#FF2B11",
        "pz": "#0D3EE0",
        "px+py": "#0BF317",
        "dz2": "#0D3EE0",
        "dxz+dyz": "#0BF317",
        "dx2y2+dxy": "#FF2B11",
    }
    FIGURE_HEIGHT = 6
    FIGURE_WIDTH = 12
    ENERGY_LIMITS = (-5, 5)


class DOSPlotConfig:
    """Configuration class for PDOS plotting.

    Attributes:
        ORBITAL_COLORS (dict): Color codes for different orbital types
        FIGURE_HEIGHT (int): Default figure height in inches
        FIGURE_WIDTH (int): Default figure width in inches
        ENERGY_LIMITS (tuple): Y-axis energy range in eV
    """
    ORBITAL_COLORS = {
        "s": "#FF00ED",
        "p": "#0BF317",
        "d": "#FF2B11",
    }
    FIGURE_HEIGHT = 6
    FIGURE_WIDTH = 12
    ENERGY_LIMITS = (-5, 5)


class CompoundNameFormatter:
    """Formats chemical compound names into LaTeX representation."""

    @staticmethod
    def format_compound_name(compound_name: str) -> str:
        """Converts a chemical formula into LaTeX format.

        Args:
            compound_name (str): Chemical formula (e.g. 'MoS2')

        Returns:
            str: LaTeX formatted compound name (e.g. '$MoS_2$')
        """

        pattern = r"(([A-Z][a-z]?)(\d?))"
        matches = re.finditer(pattern, compound_name)

        element_names = []
        element_numbers = []
        for element in matches:
            element_names.append(element.group(2))
            element_numbers.append(1 if element.group(3) == "" else int(element.group(3)))

        latex_name = r"$"
        for name, number in zip(element_names, element_numbers):
            latex_name += r"{" + rf"{name}" + r"}"
            if number != 1:
                latex_name += r"_" + r"{" + rf"{number}" + r"}"
        latex_name += r"$"

        return latex_name


class BandPlotter:
    """Class for plotting band structure diagrams.

    This class provides methods for plotting both regular and orbital-projected
    band structures from DFT calculations.

    Args:
        config (PlotConfig, optional): Configuration object containing plot parameters
    """

    def __init__(self, config: BandsPlotConfig = None) -> None:
        """Initialize the BandPlotter with configuration.

        Args:
            config (BandsPlotConfig, optional): Configuration object with plot parameters.
                If None, the default PlotConfig will be used.
        """
        self.config = config or BandsPlotConfig()

    def init_subplot(self, ax: matplotlib.axes.Axes, xlabel: str, ylabel: str, title: str):
        """Initialize a subplot with basic settings.

        Args:
            ax (matplotlib.axes.Axes): Subplot axes object
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
            title (str): Subplot title
        """
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(self.config.HIGH_SYMMETRY_K_POINTS, self.config.K_LABELS)
        ax.grid("on")

    @staticmethod
    def plot_bands(ax: matplotlib.axes.Axes,
                   xdata: np.ndarray,
                   ydata: np.ndarray,
                   data_label: str = "data",
                   color: str = "blue") -> matplotlib.collections.PathCollection:
        """Plot regular band structure.

        Args:
            ax (matplotlib.axes.Axes): Subplot axes object
            xdata (ndarray): K-point coordinates
            ydata (ndarray): Energy values
            data_label (str, optional): Legend label. Defaults to "data"
            color (str, optional): Line color. Defaults to "blue"

        Returns:
            matplotlib.collections.PathCollection: Label handle for legend
        """
        label = ax.scatter([], [], label=data_label, color=color)

        # Plot each band as a line
        for band in range(len(ydata)):
            ax.plot(xdata, ydata[band, :], color=color)

        return label

    @staticmethod
    def plot_projected_bands(ax: matplotlib.axes.Axes,
                             xdata: np.ndarray,
                             ydata: np.ndarray,
                             orbital_weights: np.ndarray,
                             number_of_bands: int,
                             spin_orbit: bool = True,
                             data_label: str = "data",
                             color: str = "blue") -> matplotlib.collections.PathCollection:
        """Plot orbital-projected band structure.

        Args:
            ax (matplotlib.axes.Axes): Subplot axes object
            xdata (ndarray): K-point coordinates
            ydata (ndarray): Energy values
            orbital_weights (ndarray): Orbital projection weights
            number_of_bands (int): Number of bands in the calculation
            spin_orbit (bool, optional): Whether to include spin-orbit coupling. Defaults to True
            data_label (str, optional): Legend label. Defaults to "data"
            color (str, optional): Plot color. Defaults to "blue"

        Returns:
            matplotlib.collections.PathCollection: Label handle for legend
        """
        label = ax.scatter([], [], label=data_label, color=color)

        # Filtering the non-zero weights
        condition = orbital_weights != 0

        # Plotting the bands
        for band in range(number_of_bands):
            x = xdata[condition[:, band]]
            y = ydata[condition[:, band], band].T

            # Multiplying the weights by a scaling factor to get thicker points
            weights = 2 * orbital_weights[condition[:, band], band]

            # Apply alpha transparency if spin-orbit coupling is enabled
            if spin_orbit:
                ax.scatter(x, y, s=weights, color=color, alpha=1)
            else:
                ax.scatter(x, y, s=weights, color=color)

        return label

    def create_band_structure_plot(self,
                                   compound_name: str,
                                   k_points: np.ndarray,
                                   energy: np.ndarray,
                                   k_points_proj: np.ndarray,
                                   energy_proj: np.ndarray,
                                   projection_data: Dict[str, Dict],
                                   number_of_bands: int,
                                   spin_orbit: bool = False,
                                   stress_amount: str = None,
                                   save_path: str = None) -> None:
        """Create a complete band structure plot with projections.

        Args:
            compound_name (str): Name of the compound
            k_points (ndarray): K-point coordinates for regular bands
            energy (ndarray): Energy values for regular bands
            k_points_proj (ndarray): K-point coordinates for projected bands
            energy_proj (ndarray): Energy values for projected bands
            projection_data (dict): Dictionary containing projection data for each element
            number_of_bands (int): Number of bands to plot
            spin_orbit (bool, optional): Whether to include spin-orbit coupling. Defaults to False
            stress_amount (str, optional): Stress amount for the plot title. Defaults to None
            save_path (str, optional): Path to save the plot. Defaults to None
        """
        # One total subplot and one for each element
        number_of_subplots = len(projection_data) + 1

        # Creating figure and subplots
        fig, axs = plt.subplots(1, number_of_subplots, sharey=True, layout="constrained")

        # Setting figure dimensions
        fig.set_figheight(self.config.FIGURE_HEIGHT)
        fig.set_figwidth(self.config.FIGURE_WIDTH)

        # Formatting compound name for plot title
        latex_name = CompoundNameFormatter.format_compound_name(compound_name)

        # Setting plot title based on spin-orbit coupling and stress
        title = f"Projected Band Structure for {latex_name}"
        if spin_orbit:
            title += " with Spin-Orbit Coupling"
        elif stress_amount and stress_amount != "1":
            title += f" with {stress_amount.replace('_', '.')}$a_0$"
        else:
            title += " without Spin-Orbit Coupling"

        fig.suptitle(title)

        # Plotting total bands in first subplot
        self.init_subplot(axs[0], "k", "E (eV)", "TOTAL")
        bands_label = self.plot_bands(axs[0], k_points, energy, "total", "blue")
        axs[0].legend(loc="lower center", handles=[bands_label])

        # Plotting projected bands for each element
        for element, element_data in projection_data.items():
            element_index = element_data["index"]

            # Initializing subplot for this element
            self.init_subplot(
                axs[element_index],
                "k",
                "E (eV)",
                element
            )

            # Plotting each orbital projection
            legend_labels = []
            for i, orbital in enumerate(element_data["projected_orbitals"]):
                label = self.plot_projected_bands(
                    axs[element_index],
                    k_points_proj,
                    energy_proj,
                    element_data["orbital_weights"][i],
                    number_of_bands,
                    spin_orbit,
                    orbital,
                    element_data["plot_colors"][i]
                )
                legend_labels.append(label)

            # Adding legend for this element
            axs[element_index].legend(loc="lower center", handles=legend_labels)

        # Setting energy limits
        plt.ylim(self.config.ENERGY_LIMITS)

        # Saving plot if path is provided
        if save_path:
            plt.savefig(save_path)


class WannierComparePlotter:
    """Class for plotting Wannier and DFT band structure comparison plots."""

    def __init__(self, config: BandsPlotConfig = None) -> None:
        """Initialize the WannierComparePlotter with configuration.

        Args:
            config (PlotConfig, optional): Configuration object with plot parameters.
                If None, the default PlotConfig will be used.
        """
        self.config = config or BandsPlotConfig()
        self.name_formatter = CompoundNameFormatter()

    def init_plot(self, compound_name: str, skip_normal: bool = False, flag: str = "") -> None:
        """Initialize plot with basic settings.

        Args:
            compound_name (str): Name of the compound
            skip_normal (bool): Whether to skip non-SOC case
            flag (str): Spin-orbit flag
        """
        plt.xlabel("k")
        plt.ylabel("E (eV)")
        plt.grid(True)

        latex_name = self.name_formatter.format_compound_name(compound_name)
        if skip_normal or flag == "_soc":
            plt.title(f"Band Structure Comparison for {latex_name} with Spin-Orbit Coupling")
        else:
            plt.title(f"Band Structure Comparison for {latex_name} without Spin-Orbit Coupling")

        plt.xticks(self.config.HIGH_SYMMETRY_K_POINTS, self.config.K_LABELS)

    def plot_comparison(self,
                        k_points_dft: np.ndarray,
                        dft_energies: np.ndarray,
                        k_points_wannier: np.ndarray,
                        wannier_energies: np.ndarray,
                        save_path: str = None) -> None:
        """Plot comparison between Wannier and DFT band structures.

        Args:
            k_points_dft (ndarray): K-point coordinates for DFT bands
            dft_energies (ndarray): Energy values for DFT bands
            k_points_wannier (ndarray): K-point coordinates for Wannier bands
            wannier_energies (ndarray): Energy values for Wannier bands
            save_path (str, optional): Path to save the plot
        """
        # Plot Wannier bands
        plt.plot([], [], color="red", label="Wannier")
        for band in range(len(wannier_energies)):
            plt.plot(k_points_wannier, wannier_energies[band, :], color="red")

        # Plot DFT bands
        plt.plot([], [], color="blue", label="DFT")
        for band in range(len(dft_energies)):
            plt.plot(k_points_dft, dft_energies[band, :], color="blue")

        plt.ylim(self.config.ENERGY_LIMITS)
        plt.legend(loc=(0.4, 0.6))

        if save_path:
            plt.savefig(save_path)


class DOSPlotter:
    """Class for plotting projected density of states (PDOS) diagrams."""

    def __init__(self, config: DOSPlotConfig = None) -> None:
        """Initialize the PdosPlotter with configuration.

        Args:
            config (PdosPlotConfig, optional): Configuration object with plot parameters.
                If None, the default PdosPlotConfig will be used.
        """
        self.config = config or DOSPlotConfig()

    def init_subplot(self, ax: matplotlib.axes.Axes, title: str) -> None:
        """Initialize a subplot with basic settings.

        Args:
            ax (matplotlib.axes.Axes): Subplot axes object
            title (str): Subplot title
        """

        ax.set_xlabel("E (eV)")
        ax.set_ylabel("PDOS")
        ax.set_title(title)
        ax.grid("on")
        ax.set_xlim(self.config.ENERGY_LIMITS)

    @staticmethod
    def plot_pdos(ax: matplotlib.axes.Axes,
                  energy: np.ndarray,
                  pdos: np.ndarray,
                  data_label: str = "data",
                  color: str = "blue",
                  ) -> None:
        """Plot projected density of states (PDOS).

        Args:
            ax (matplotlib.axes.Axes): Subplot axes object
            energy (ndarray): Energy values
            pdos (ndarray): PDOS values
            data_label (str): Label for the data
            color (str): Color for the data
        """

        # Plot and fill DOS
        ax.plot(energy, pdos, label=data_label, color=color)
        ax.fill_between(energy, 0, pdos, color=color, alpha=0.15)
        ax.legend(loc="best")

    def create_pdos_plot(self,
                         compound_name: str,
                         energy: np.ndarray,
                         pdos_total: np.ndarray,
                         projection_data: Dict[str, Dict],
                         spin_orbit: bool = False,
                         save_path: str = None) -> None:
        """Create a complete PDOS plot with projections.

        Args:
            compound_name (str): Name of the compound
            energy (ndarray): Energy values for DOS
            pdos_total (ndarray): Total DOS values
            projection_data (dict): Dictionary containing projection data for each element
            spin_orbit (bool, optional): Whether to include spin-orbit coupling
            save_path (str, optional): Path to save the plot
        """
        # One total subplot and one for each element
        number_of_subplots = len(projection_data) + 1

        # Creating figure and subplots
        fig, axs = plt.subplots(1, number_of_subplots, sharey=True, layout="constrained")

        # Setting figure dimensions
        fig.set_figheight(self.config.FIGURE_HEIGHT)
        fig.set_figwidth(self.config.FIGURE_WIDTH)

        # Formatting compound name for plot title
        latex_name = CompoundNameFormatter.format_compound_name(compound_name)

        # Setting plot title based on spin-orbit coupling
        title = f"Projected DOS for {latex_name}"
        if spin_orbit:
            title += " with Spin-Orbit Coupling"
        else:
            title += " without Spin-Orbit Coupling"

        fig.suptitle(title)

        # Plotting total DOS in first subplot
        self.init_subplot(axs[0], "TOTAL")
        self.plot_pdos(axs[0], energy, pdos_total, "total", "black")

        # Plotting projected DOS for each element
        for element, element_data in projection_data.items():
            element_index = element_data["index"]

            # Initializing subplot for this element
            self.init_subplot(axs[element_index], element)

            # Plotting each orbital projection
            for orbital, color, pdos in zip(
                    element_data["projected_orbitals"],
                    element_data["plot_colors"],
                    element_data["pdos"]
            ):
                self.plot_pdos(
                    axs[element_index],
                    energy,
                    pdos,
                    f"{element}-{orbital}",
                    color
                )

        # Saving plot if path is provided
        if save_path:
            plt.savefig(save_path)


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
            self.config = config or BandsPlotConfig()
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

            for orbital, color in self.config.ORBITAL_COLORS.items():
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

            for orbital, color in self.config.ORBITAL_COLORS.items():
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
                        plot_config: BandsPlotConfig = BandsPlotConfig(),
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
    # Initializing objects for plotting and processing projection data
    plotter = BandPlotter(plot_config)
    processor = ProjectionDataProcessor(
        plot_config,
        project.band_data.unique_elements,
        weights_info_list=project.band_data.atomic_projection_weights
    )

    # Process projection data into a structured format
    projection_info_list = processor.process_projections()

    # Extracting configuration values
    compound_name = project.compound_name
    spin_orbit_flags = project.band_info.spin_orbit_flags if project.band_info.spin_orbit_flags else [False] * len(
        project.band_data.energy)
    stress_amount_list = (["1"] + project.stress_amounts) if project.include_stress else ["1"] * len(
        project.band_data.energy)

    if test_module:
        # Debug mode: Printing projection information for verification
        print("\nProjection info list prepared for plotting. Orbital weights are not printed:")
        for projection_info, spin_orbit_flag, stress_amount in zip(projection_info_list, spin_orbit_flags,
                                                                   stress_amount_list):
            if project.include_stress:
                print(f"\nStress amount: {(float(stress_amount.replace('_', '.')) * 100):.2f}%")
            else:
                if spin_orbit_flag:
                    print("\nWith SOC:")
                else:
                    print("\nWithout SOC:")

            for atom, info in projection_info.items():
                # Not printing the orbital weights as it takes a lot of space
                debug_info = {key: value for key, value in info.items() if key != "orbital_weights"}
                print(f"{atom}: {debug_info}")
    else:
        # Plotting mode: Generating plots for each dataset
        for (projection_data, k_points, energy, k_points_proj, energy_proj,
             number_of_bands, spin_orbit, stress_amount) in zip(
            projection_info_list,
            project.band_data.k_points,
            project.band_data.energy,
            project.band_data.k_points_proj,
            project.band_data.energy_proj,
            project.band_info.number_of_bands,
            spin_orbit_flags,
            stress_amount_list):

            if save_fig:
                # Generating file name for saving the plot
                if spin_orbit:
                    file_name = f"{compound_name}_projbands_soc.png"
                elif stress_amount != "1":
                    file_name = f"{compound_name}_projbands{stress_amount}.png"
                else:
                    file_name = f"{compound_name}_projbands.png"

                save_path = os.path.join(project.project_dir, file_name)

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

            else:
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


def plot_wannier_comparison(project: ProjectSetup,
                            plot_config: BandsPlotConfig = BandsPlotConfig(),
                            save_fig: bool = True,
                            test_module: bool = False) -> None:
    """Plot Wannier and DFT band structure comparison.

    Args:
        project (ProjectSetup): Project configuration and data container
        plot_config (BandsPlotConfig, optional): Plotting configuration. Defaults to BandsPlotConfig().
        save_fig (bool, optional): Whether to save the plots to files. Defaults to True.
        test_module (bool, optional): If True, prints debug information instead of plotting. Defaults to False.
    """
    plotter = WannierComparePlotter(plot_config)
    comparison_data = project.wannier_setup.comparison_data
    spin_orbit_flags = ["_soc"] if project.wannier_setup.skip_normal else ["", "_soc"]

    if test_module:
        print("\nComparison data prepared for plotting. The plotting data is not printed:")

        for fermi_energy, alat_parameter, flag in zip(
                project.wannier_setup.fermi_energies,
                project.wannier_setup.alat_parameters,
                spin_orbit_flags
        ):
            print(f"Fermi energy: {fermi_energy} eV")
            print(f"Lattice parameter: {alat_parameter} Å")
            print(f"Spin-orbit flag: {flag}")

        print(f"Skip normal: {project.wannier_setup.skip_normal}")

    else:
        if save_fig:
            for k_points_dft, dft_energies, k_points_wannier, wannier_energies, flag in zip(
                    comparison_data["k_points_dft"],
                    comparison_data["dft_energies"],
                    comparison_data["k_points_wannier"],
                    comparison_data["wannier_energies"],
                    spin_orbit_flags
            ):
                save_path = os.path.join(
                    project.project_dir,
                    f"{project.compound_name}_comparison{flag}.png"
                )

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

        else:
            for k_points_dft, dft_energies, k_points_wannier, wannier_energies, flag in zip(
                    comparison_data["k_points_dft"],
                    comparison_data["dft_energies"],
                    comparison_data["k_points_wannier"],
                    comparison_data["wannier_energies"],
                    spin_orbit_flags
            ):
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


def plot_pdos(project: ProjectSetup,
              plot_config: DOSPlotConfig = DOSPlotConfig(),
              save_fig: bool = False,
              test_module: bool = False) -> None:
    """Plot projected DOS.

    Args:
        project (ProjectSetup): Project configuration and data container
        plot_config (PDOSPlotConfig, optional): Plotting configuration. Defaults to PDOSPlotConfig().
        save_fig (bool, optional): Whether to save the plots to files. Defaults to False.
        test_module (bool, optional): If True, prints debug information instead of plotting. Defaults to False.
    """
    compound_name = project.compound_name
    spin_orbit_flags = ["", "_soc"]
    projection_processor = AtomicProjectionProcessor(list(project.dos_setup.atomic_states_info[0].keys()))
    unique_elements_list = projection_processor.get_unique_elements()

    projection_data_processor = ProjectionDataProcessor(plot_config,
                                                        unique_elements_list,
                                                        is_pdos=True,
                                                        pdos_info_list=project.dos_setup.atomic_states_info,
                                                        dos_data_list=project.dos_setup.dos_data
                                                        )

    projection_data_list = projection_data_processor.process_projections()

    if test_module:

        print("\nProjection data prepared for plotting. The plotting data is not printed:")
        print(f"\nUnique elements: {unique_elements_list}\n")

        for projection_data, flag in zip(projection_data_list, spin_orbit_flags):
            plotting_info = {element: {key: value for key, value in element_data.items()
                             if key in ["index", "projected_orbitals", "plot_colors"]}
                   for element, element_data in projection_data.items()}
            print(f"Spin-orbit flag: {'SOC' if flag == '_soc' else 'Non-SOC'}\n")
            for element, element_data in plotting_info.items():
                print(f"Element: {element}")
                print(f"Index: {element_data['index']}")
                print(f"Projected orbitals: {element_data['projected_orbitals']}")
                print(f"Plot colors: {element_data['plot_colors']}\n")

    else:

        plotter = DOSPlotter(plot_config)

        if save_fig:
            for projection_data, flag in zip(projection_data_list, spin_orbit_flags):
                save_path = os.path.join(
                    project.project_dir,
                    f"{compound_name}_pdos{flag}.png"
                )

                # Get total DOS from first element's energy values
                energy = projection_data[unique_elements_list[0]]["energies"][0]
                pdos_total = np.zeros_like(energy)

                # Sum up all orbital contributions for total DOS
                for element_data in projection_data.values():
                    for pdos in element_data["pdos"]:
                        pdos_total += pdos

                # Create and save the plot
                plotter.create_pdos_plot(
                    compound_name,
                    energy,
                    pdos_total,
                    projection_data,
                    flag == "_soc",
                    save_path
                )

        else:

            # Displaying plots without saving
            for projection_data, flag in zip(projection_data_list, spin_orbit_flags):

                # Getting total DOS from first element's energy values
                energy = projection_data[unique_elements_list[0]]["energies"][0]
                pdos_total = np.zeros_like(energy)

                # Summing up all orbital contributions for total DOS
                for element_data in projection_data.values():
                    for pdos in element_data["pdos"]:
                        pdos_total += pdos

                # Creating and displaying the plot
                plotter.create_pdos_plot(
                    compound_name,
                    energy,
                    pdos_total,
                    projection_data,
                    flag == "_soc"
                )
                plt.show()

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
    # Check if the script is being run for input generation (3 arguments passed)
    os.chdir("..")
    is_input = len(argv) == 3

    response = input("Enter the initialization type you want to test for (wannier, bands, pdos): ").strip().lower()

    match response:
        case "wannier":
            project = initialize_project(argv, is_input, is_wannier=True)
            prepare_wannier_info(project)
            process_comparison_data(project)

            plot_config = BandsPlotConfig()
            plot_wannier_comparison(project, plot_config, save_fig=False, test_module=True)

        case "bands":
            project = initialize_project(argv, is_input)
            prepare_bands_info(project)
            process_band_data(project)

            plot_config = BandsPlotConfig()
            plot_band_structure(project, plot_config, save_fig=False, test_module=True)

        case "pdos":
            project = initialize_project(argv, is_input, is_pdos=True)
            prepare_pdos_info(project)
            process_pdos_data(project)

            plot_config = DOSPlotConfig()
            plot_pdos(project, plot_config, save_fig=False, test_module=True)

        case _:
            raise ValueError("Invalid input!")