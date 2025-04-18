"""Module for handling the plotting of processed data from DFT calculations."""

import re
import os
import matplotlib.pyplot as plt
from data_processor import process_band_data
from dft_info_extractor import prepare_dft_info
from path_handler import prepare_paths


class PlotConfig:
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
    ENERGY_LIMITS = (-3, 3)


class CompoundNameFormatter:
    """Formats chemical compound names into LaTeX representation."""

    @staticmethod
    def format_compound_name(compound_name):
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

    def __init__(self, config=None):
        """Initialize the BandPlotter with configuration.

        Args:
            config (PlotConfig, optional): Configuration object with plot parameters.
                If None, the default PlotConfig will be used.
        """
        self.config = config or PlotConfig()

    def init_subplot(self, ax, xlabel, ylabel, title):
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
    def plot_bands(ax, xdata, ydata, data_label="data", color="blue"):
        """Plot regular band structure.

        Args:
            ax (matplotlib.axes.Axes): Subplot axes object
            xdata (ndarray): K-point coordinates
            ydata (ndarray): Energy values
            data_label (str, optional): Legend label. Defaults to "data"
            color (str, optional): Line color. Defaults to "blue"

        Returns:
            matplotlib.lines.Line2D: Label handle for legend
        """
        label = ax.scatter([], [], label=data_label, color=color)

        # Plot each band as a line
        for band in range(len(ydata)):
            ax.plot(xdata, ydata[band, :], color=color)

        return label

    @staticmethod
    def plot_projected_bands(ax, xdata, ydata, orbital_weights, number_of_bands,
                             spin_orbit=True, data_label="data", color="blue"):
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
            matplotlib.lines.Line2D: Label handle for legend
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

    def create_band_structure_plot(self, compound_name, k_points, energy, k_points_proj,
                                   energy_proj, projection_data, number_of_bands,
                                   spin_orbit=False, stress_amount=None, save_path=None):
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

        Returns:
            tuple: Figure and axes objects
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
        axs[0].legend(handles=[bands_label])

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

        return fig, axs


class ProjectionDataProcessor:
    """Processes atomic projection data for band structure plotting.

    This class handles the processing of atomic projection weights and organizing
    them by element and orbital type for visualization.

    Args:
        atomic_projection_weights_info_list (list): List of dictionaries containing projection weights
        unique_elements_list (list): List of unique chemical elements
    """

    def __init__(self, atomic_projection_weights_info_list, unique_elements_list):
        """Initialize the ProjectionDataProcessor.

        Args:
            atomic_projection_weights_info_list (list): List of dictionaries containing projection weights
            unique_elements_list (list): List of unique chemical elements
        """
        self.weights_info_list = atomic_projection_weights_info_list
        self.elements_list = unique_elements_list
        self.orbital_colors = self._get_orbital_colors()

    @staticmethod
    def _get_orbital_colors():
        """Get the color mapping for different orbital types.

        Returns:
            dict: Dictionary mapping orbital types to color codes
        """
        return PlotConfig.ORBITAL_COLORS

    def process_projections(self):
        """Process projection data for all elements.

        Returns:
            list: List of processed projection data dictionaries
        """
        projection_info_list = []

        for weights_info in self.weights_info_list:
            projection_info = {}

            for i, element in enumerate(self.elements_list):
                projection_info[element] = self._process_element_projections(
                    weights_info, element, i)

            projection_info_list.append(projection_info)

        return projection_info_list

    def _process_element_projections(self, weights_info, element, index):
        """Process projection data for a single element.

        Args:
            weights_info (dict): Dictionary containing projection weights
            element (str): Chemical element symbol
            index (int): Element index

        Returns:
            dict: Processed projection data for the element
        """
        orbitals = []
        colors = []
        weights = []

        for orbital, color in self.orbital_colors.items():
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

    @staticmethod
    def combine_similar_orbitals(weights_info):
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


def plot_band_structure(updated_config, save_fig=True, test_module=False):
    """
    Plot band structure from processed data.

    Args:
        updated_config (dict): Configuration dictionary containing processed data. Expected keys include:
            - "atomic_projection_weights_info_list" (list): List of atomic projection weights.
            - "unique_elements_list" (list): List of unique chemical elements.
            - "compound_name" (str): Name of the compound.
            - "spin_orbit_flags" (list, optional): Flags indicating spin-orbit coupling for each dataset.
            - "stress_amounts" (list, optional): List of stress amounts for each dataset.
            - "include_stress" (bool): Whether to include stress in the plots.
            - "k_points_list" (list): List of k-point coordinates for each dataset.
            - "energy_list" (list): List of energy values for each dataset.
            - "k_points_proj_list" (list): List of k-point coordinates for projected bands.
            - "energy_proj_list" (list): List of energy values for projected bands.
            - "number_of_bands_list" (list): List of the number of bands for each dataset.
            - "project_dir" (str): Directory to save the plots.
        save_fig (bool, optional): Whether to save the plots to files. Defaults to True.
        test_module (bool, optional): If True, prints debug information instead of plotting. Defaults to False.
    """
    # Initializing objects for plotting and processing projection data
    plotter = BandPlotter()
    processor = ProjectionDataProcessor(
        updated_config["atomic_projection_weights_info_list"],
        updated_config["unique_elements_list"]
    )

    # Process projection data into a structured format
    projection_info_list = processor.process_projections()

    # Extracting configuration values
    compound_name = updated_config["compound_name"]
    spin_orbit_flags = updated_config.get("spin_orbit_flags", [False] * len(updated_config["energy_list"]))
    stress_amount_list = (["1"] + updated_config["stress_amounts"]) if updated_config["include_stress"] else [
                                                                                                                 "1"] * len(
        updated_config["energy_list"])

    if test_module:
        # Debug mode: Printing projection information for verification
        print("\nProjection info list prepared for plotting. Orbital weights are not printed:")
        for projection_info, spin_orbit_flag, stress_amount in zip(projection_info_list, spin_orbit_flags,
                                                                   stress_amount_list):
            if updated_config["include_stress"]:
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
            updated_config["k_points_list"],
            updated_config["energy_list"],
            updated_config["k_points_proj_list"],
            updated_config["energy_proj_list"],
            updated_config["number_of_bands_list"],
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

                save_path = os.path.join(updated_config["project_dir"], file_name)

                # Creating and saveing the plot
                fig, axs = plotter.create_band_structure_plot(
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
                fig, axs = plotter.create_band_structure_plot(
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


if __name__ == "__main__":
    """
    Main entry point for the script. Prepares configuration, processes data, and plots band structures.

    Steps:
        1. Prepare paths for input and output files.
        2. Extract DFT information from input files.
        3. Process band data for plotting.
        4. Call the `plot_band_structure` function to generate plots.
    """
    config = prepare_paths()
    config = prepare_dft_info(config)
    config = process_band_data(
        config,
        config["paths"]["projbands_paths"],
        config["paths"]["bands_paths"],
        config["number_of_bands_list"],
        config["fermi_energy_list"],
        config["project_dir"],
        config["atomic_states_info_list"],
        config["atomic_states_info_list"][0].keys()
    )
    plot_band_structure(config, save_fig=False, test_module=True)
