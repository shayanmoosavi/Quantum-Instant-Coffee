"""Module for processing the data collected from Quantum ESPRESSO output files."""

from dft_info_extractor import *
import numpy as np


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
            projbands_dir (str): Path to the projected bands file.
            number_of_bands (int): Number of bands in the data.

        Returns:
            tuple: A tuple containing:
                - projbands_data (ndarray): The raw projected bands data.
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
        elements = [proj[0] for proj in self.atomic_projection_list]
        return [item for i, item in enumerate(elements) if item not in elements[:i]]

    @staticmethod
    def process_orbital_weights(atomic_states_info, weight_calculator, projbands_data, number_of_bands):
        """
        Process orbital weights for atomic projections.

        Args:
            atomic_states_info (dict): Information about atomic projections.
            weight_calculator (WeightCalculator): Instance of WeightCalculator.
            projbands_data (ndarray): The projected bands data.
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


def process_band_data(config, projbands_dir_list, bands_dir_list, number_of_bands_list,
                      fermi_energy_list, project_dir, atomic_projection_info_list,
                      atomic_projection_list):
    """
    Process all band data and calculate projections.

    Args:
        config (dict): Configuration dictionary generated by the previous steps.
        projbands_dir_list (list): List of paths to projected bands files.
        bands_dir_list (list): List of paths to bands files.
        number_of_bands_list (list): List of the number of bands for each file.
        fermi_energy_list (list): List of Fermi energy values.
        project_dir (str): The directory containing the project files.
        atomic_projection_info_list (list): List of atomic projection information.
        atomic_projection_list (list): List of atomic projections.

    Returns:
        dict: Updated configuration dictionary containing:
            - projbands_data_list (list): List of projected bands data.
            - k_points_proj_list (list): List of unique k-points from projected bands.
            - k_points_list (list): List of unique k-points from bands data.
            - energy_proj_list (list): List of reshaped energy data for projected bands.
            - energy_list (list): List of reshaped energy data for bands.
            - atomic_projection_weights_info_list (list): List of atomic projection weights information.
    """
    processor = BandDataProcessor(project_dir)
    calculator = WeightCalculator()
    projection_processor = AtomicProjectionProcessor(atomic_projection_list)

    projbands_data_list = []
    k_points_proj_list = []
    k_points_list = []
    energy_proj_list = []
    energy_list = []
    atomic_projection_weights_info_list = []

    for projbands_dir, bands_dir, num_bands, fermi_energy, proj_info in zip(
            projbands_dir_list, bands_dir_list, number_of_bands_list,
            fermi_energy_list, atomic_projection_info_list
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

        # Updating the configuration with the processed data
        config["projbands_data_list"] = projbands_data_list,
        config["k_points_proj_list"] = k_points_proj_list,
        config["k_points_list"] = k_points_list,
        config["energy_proj_list"] = energy_proj_list,
        config["energy_list"] = energy_list,
        config["atomic_projection_weights_info_list"] = atomic_projection_weights_info_list
        config["atomic_projection_list"] = atomic_projection_list

    return config


# Testing to ensure the module works as expected
if __name__ == "__main__":

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
    print("Data processed successfully and ready for plotting.")
