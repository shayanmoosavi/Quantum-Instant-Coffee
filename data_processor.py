"""Module for processing the data collected from Quantum ESPRESSO output files.

This module provides classes and functions to process band structure data and atomic projections
from Quantum ESPRESSO output files. It includes functionality for loading data, calculating orbital
weights, and processing atomic projections.
"""

from dft_info_extractor import *
import numpy as np
from models import BandData


class BandDataProcessor:
    """
    Handles loading and processing of band structure data.

    Attributes:
        project_dir (str): The directory containing the project files.
    """

    def __init__(self, project_dir):
        """
        Initialize the BandDataProcessor with the project directory.

        Args:
            project_dir (str): The directory containing the project files.
        """
        self.project_dir = project_dir

    @staticmethod
    def load_projected_bands(projbands_dir, number_of_bands):
        """
        Load and process projected bands data from a file.

        Args:
            projbands_dir (str): Path to the generated projbands file.
            number_of_bands (int): Number of bands in the data.

        Returns:
            tuple: A tuple containing:
                - projbands_data (ndarray): The raw projbands data.
                - k_points_proj (ndarray): Unique k-points from the data.
                - energy_proj (ndarray): Reshaped energy data for the bands.
        """
        projbands_data = np.loadtxt(projbands_dir)
        k_points_proj = np.unique(projbands_data[:, 1])
        energy_proj = np.reshape(projbands_data[:, 2], (-1, number_of_bands))
        return projbands_data, k_points_proj, energy_proj

    @staticmethod
    def load_bands(bands_dir, fermi_energy):
        """
        Load and process bands data from a file.

        Args:
            bands_dir (str): Path to the bands file.
            fermi_energy (float): The Fermi energy value.

        Returns:
            tuple: A tuple containing:
                - bands_data (ndarray): The raw bands data.
                - k_points (ndarray): Unique k-points from the data.
                - energy (ndarray): Reshaped energy data adjusted by the Fermi energy.
        """
        bands_data = np.loadtxt(bands_dir)
        k_points = np.unique(bands_data[:, 0])
        energy = np.reshape(bands_data[:, 1], (-1, len(k_points))) - fermi_energy
        return bands_data, k_points, energy


class WeightCalculator:
    """Handles orbital weight calculations for band structure."""

    @staticmethod
    def calculate_total_weights(data, atomic_state_indices, atomic_state_coefficients, number_of_bands):
        """
        Calculate weights of specified orbitals from projected bands data.

        Args:
            data (ndarray): The projected bands data.
            atomic_state_indices (list): Indices of the atomic states.
            atomic_state_coefficients (list): Coefficients for the atomic states.
            number_of_bands (int): Number of bands in the data.

        Returns:
            ndarray: Reshaped total orbital weights for the bands.
        """
        # Initializing the array
        total_orbital_weights = np.zeros(len(data[:, 0]))

        # Calculating the total weights for each atomic state
        for index in atomic_state_indices:
            for coefficient in atomic_state_coefficients:

                # The first 3 columns are not the weights
                total_orbital_weights += coefficient * data[:, index + 3]

        return np.reshape(total_orbital_weights, (-1, number_of_bands))


class AtomicProjectionProcessor:
    """
    Processes atomic projections and their weights.

    Attributes:
        atomic_projection_list (list): List of atomic projections.
    """

    def __init__(self, atomic_projection_list):
        """
        Initialize the AtomicProjectionProcessor with a list of atomic projections.

        Args:
            atomic_projection_list (list): List of atomic projections.
        """
        self.atomic_projection_list = atomic_projection_list

    def get_unique_elements(self):
        """
        Extract unique elements from atomic projections.

        Returns:
            list: A list of unique elements.
        """
        elements = [proj.split('-')[0] for proj in self.atomic_projection_list]
        return [item for i, item in enumerate(elements) if item not in elements[:i]]

    @staticmethod
    def process_orbital_weights(atomic_states_info, weight_calculator, projbands_data, number_of_bands):
        """
        Process orbital weights for atomic projections.

        Args:
            atomic_states_info (dict): Information about atomic projections.
            weight_calculator (WeightCalculator): Instance of WeightCalculator.
            projbands_data (ndarray): The projbands data.
            number_of_bands (int): Number of bands in the data.

        Returns:
            dict: A dictionary mapping atomic projections to their total orbital weights.
        """
        weights_info = {}

        for atomic_projection, proj_info in atomic_states_info.items():
            total_weight = weight_calculator.calculate_total_weights(
                projbands_data,
                proj_info["indices"],
                proj_info["coefficients"],
                number_of_bands
            )

            atom, orbital = atomic_projection.split("-")
            key = f"{atom}-{orbital}" if orbital not in ["px", "py", "dxz", "dyz", "dx2y2", "dxy"] else {
                "px": f"{atom}-px+py",
                "py": f"{atom}-px+py",
                "dxz": f"{atom}-dxz+dyz",
                "dyz": f"{atom}-dxz+dyz",
                "dx2y2": f"{atom}-dx2y2+dxy",
                "dxy": f"{atom}-dx2y2+dxy"
            }[orbital]

            weights_info[key] = total_weight

        return weights_info


def process_band_data(project):
    """
    Process all band data and calculate projections.

    Args:
        project (ProjectSetup): Project configuration and data container

    Returns:
        ProjectSetup: Updated project configuration with processed band data
    """
    processor = BandDataProcessor(project.project_dir)
    calculator = WeightCalculator()
    projection_processor = AtomicProjectionProcessor(project.dft_info.atomic_states_info[0].keys())

    projbands_data_list = []
    k_points_proj_list = []
    k_points_list = []
    energy_proj_list = []
    energy_list = []
    atomic_projection_weights_info_list = []

    for projbands_dir, bands_dir, num_bands, fermi_energy, proj_info in zip(
            project.output_paths["projbands_paths"],
            project.output_paths["bands_paths"],
            project.dft_info.number_of_bands,
            project.dft_info.fermi_energies,
            project.dft_info.atomic_states_info
    ):
        # Loading and processing of data
        projbands_data, k_points_proj, energy_proj = processor.load_projected_bands(
            projbands_dir, num_bands)
        _, k_points, energy = processor.load_bands(bands_dir, fermi_energy)

        # Calculating weights
        weights_info = projection_processor.process_orbital_weights(
            proj_info, calculator, projbands_data, num_bands)

        # Storing results
        projbands_data_list.append(projbands_data)
        k_points_proj_list.append(k_points_proj)
        k_points_list.append(k_points)
        energy_proj_list.append(energy_proj)
        energy_list.append(energy)
        atomic_projection_weights_info_list.append(weights_info)

    # Get unique elements from the atomic projection list
    unique_elements_list = projection_processor.get_unique_elements()

    # Create band data container
    band_data = BandData(
        projbands_data=projbands_data_list,
        k_points_proj=k_points_proj_list,
        k_points=k_points_list,
        energy_proj=energy_proj_list,
        energy=energy_list,
        atomic_projection_weights=atomic_projection_weights_info_list,
        atomic_projections=list(project.dft_info.atomic_states_info[0].keys()),
        unique_elements=unique_elements_list
    )

    project.band_data = band_data

    return project


# Testing to ensure the module works as expected
if __name__ == "__main__":
    """
    Main entry point for testing the module.

    This script validates the processing of band data and ensures that the
    atomic projections and weights are calculated correctly.
    """
    is_input = len(argv) == 3

    project = initialize_project(argv, is_input)
    prepare_dft_info(project)

    process_band_data(project)

    print("Data processed successfully and ready for plotting.")
    print(f"Elements: {project.band_data.unique_elements}")
