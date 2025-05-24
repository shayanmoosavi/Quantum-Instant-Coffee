""" Module for plotter classes.

This module provides classes for plotting electronic band structures,
comparison plots between Wannier and DFT calculations, and projected
density of states (PDOS). It includes functionalities for formatting
compound names into LaTeX for better presentation. The module uses
matplotlib for creating the plots and includes configuration options
for customizing the appearance of the plots.

Classes:
    CompoundNameFormatter: Formats chemical compound names into LaTeX representation.
    BandPlotter: Plots band structure diagrams, including regular and orbital-projected bands.
    WannierComparePlotter: Plots comparison plots between Wannier and DFT band structures.
    DOSPlotter: Plots projected density of states (PDOS) diagrams.
"""
import re
from typing import Dict

import matplotlib.axes
import matplotlib.collections
import numpy as np
from matplotlib import pyplot as plt

from core.config_handler import BandsPlotConfig, DOSPlotConfig


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
        self.config = config or BandsPlotConfig.get_default_config()

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
        ax.set_xticks(self.config.high_symmetry_points, self.config.k_labels)
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

            weights = orbital_weights[condition[:, band], band]

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
        fig.set_figheight(self.config.figure_height)
        fig.set_figwidth(self.config.figure_width)

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
        plt.ylim(self.config.energy_limits)

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
        self.config = config or BandsPlotConfig.get_default_config()
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

        plt.xticks(self.config.high_symmetry_points, self.config.k_labels)

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

        plt.ylim(self.config.energy_limits)
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
        self.config = config or DOSPlotConfig.get_default_config()

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
        ax.set_xlim(self.config.energy_limits)

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
        fig.set_figheight(self.config.figure_height)
        fig.set_figwidth(self.config.figure_width)

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