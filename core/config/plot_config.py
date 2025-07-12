""" Module containing classes for plotting configurations.

This module defines the BandsPlotConfig and DOSPlotConfig classes, which are used to manage plot configurations.
It includes methods for loading configurations from YAML files, merging user-defined values with default values,
and validating the configuration structure.
"""
from dataclasses import dataclass
from typing import Dict, Tuple, List

from yaml import safe_load

from ui.ui_helpers import print_error, print_warning
from utils.config_validation import validate_plot_config_structure, ConfigValidationError


def overwrite_plot_config_values(default_config: Dict, user_config: Dict) -> Dict:
    """
    Recursively overwrites default configuration values with user-defined values.
    Args:
        default_config (Dict): The default configuration dictionary.
        user_config (Dict): The user-defined configuration dictionary.

    Returns:
        Dict: The merged configuration dictionary.
    """
    for key, value in user_config.items():
        if isinstance(value, Dict) and key in default_config and isinstance(default_config[key], Dict):
            default_config[key] = overwrite_plot_config_values(default_config[key], value)
        else:
            default_config[key] = value
    return default_config


@dataclass
class BandsPlotConfig:
    """Configuration class containing constants for plot styling and parameters.

    Attributes:
        high_symmetry_points (list): K-point coordinates for high symmetry points in k-space
        k_labels (list): LaTeX formatted labels for high symmetry k-points
        orbital_colors (dict): Color codes for different orbital types
        figure_height (int): Default figure height in inches
        figure_width (int): Default figure width in inches
        energy_limits (tuple): Y-axis energy range in eV
    """
    high_symmetry_points: List[float]
    k_labels: List[str]
    orbital_colors: Dict[str, str]
    figure_height: int
    figure_width: int
    energy_limits: Tuple

    @classmethod
    def from_yaml(cls, config_file: str = "plot_config.yaml") -> 'BandsPlotConfig':
        """Creates configuration from YAML file."""
        default_config_instance = cls.get_default_config()
        default_config_dict = default_config_instance.__dict__
        try:

            with open(config_file, 'r') as f:
                user_config = safe_load(f)

            validate_plot_config_structure(user_config, plot_config_type="bands")

            user_bands_plot_config = user_config['bands_plot']

            # Merging user config with default config
            merged_config_dict = overwrite_plot_config_values(default_config_dict.copy(), user_bands_plot_config)

            # Reconstructing k_labels with LaTeX formatting if they were overridden
            if 'k_labels' in user_bands_plot_config:
                merged_config_dict['k_labels'] = [
                    r"$\{}$".format(label) if label == "Gamma" else r"${}$".format(label)
                    for label in merged_config_dict['k_labels']
                ]

            # Reconstructing energy_limits as a tuple
            if 'figure' in user_bands_plot_config:
                if 'energy_limits' in user_bands_plot_config['figure']:
                    merged_config_dict['energy_limits'] = tuple(merged_config_dict['figure']['energy_limits'])

            # Extracting figure height and width from the merged 'figure' dictionary
            merged_config_dict['figure_height'] = merged_config_dict['figure']['height']
            merged_config_dict['figure_width'] = merged_config_dict['figure']['width']
            del merged_config_dict['figure']

            return cls(
                high_symmetry_points=merged_config_dict['high_symmetry_points'],
                k_labels=merged_config_dict['k_labels'],
                orbital_colors=merged_config_dict['orbital_colors'],
                figure_height=merged_config_dict['figure_height'],
                figure_width=merged_config_dict['figure_width'],
                energy_limits=merged_config_dict['energy_limits'])

        except ConfigValidationError as e:
            print_error("An error occurred while validating the configuration file:")
            print_error(f"{str(e)}")
            print_warning("Using default configuration instead.")
            return cls.get_default_config()

        except FileNotFoundError:
            print_warning(f"Config file not found at `{config_file}`. Using default configuration.")
            return cls.get_default_config()

        except Exception as e:
            print_error(f"Unexpected error while loading config file:")
            print_error(f"{str(e)}")
            print_warning("Using default configuration instead.")
            return cls.get_default_config()

    @classmethod
    def get_default_config(cls) -> 'BandsPlotConfig':
        """Create configuration with default values."""
        return cls(
            high_symmetry_points=[0.0000, 0.5774, 0.9107, 1.5774],
            k_labels=[r"$\Gamma$", r"$M$", r"$K$", r"$\Gamma$"],
            orbital_colors={
                "s": "#FF00ED",
                "p": "#0BF317",
                "d": "#FF2B11",
                "pz": "#0D3EE0",
                "px+py": "#0BF317",
                "dz2": "#0D3EE0",
                "dxz+dyz": "#0BF317",
                "dx2y2+dxy": "#FF2B11",
                "all": "#FBFF2F"
            },
            figure_height=6,
            figure_width=12,
            energy_limits=(-5, 5)
        )


@dataclass
class DOSPlotConfig:
    """Configuration class for PDOS plotting.

    Attributes:
        orbital_colors (dict): Color codes for different orbital types
        figure_height (int): Default figure height in inches
        figure_width (int): Default figure width in inches
        energy_limits (tuple): X-axis energy range in eV
        dos_limits (tuple, optional): Y-axis DOS range in states/eV (default is None)
    """
    orbital_colors: Dict[str, str]
    figure_height: int
    figure_width: int
    energy_limits: Tuple
    dos_limits: Tuple

    @classmethod
    def from_yaml(cls, config_file: str = "plot_config.yaml") -> 'DOSPlotConfig':
        """Creates configuration from YAML file."""
        default_config_instance = cls.get_default_config()
        default_config_dict = default_config_instance.__dict__

        try:
            with open(config_file, 'r') as f:
                user_config = safe_load(f)

            validate_plot_config_structure(user_config, plot_config_type="dos")

            user_dos_plot_config = user_config['dos_plot']

            # Merging user config with default config
            merged_config_dict = overwrite_plot_config_values(default_config_dict.copy(), user_dos_plot_config)

            # Reconstructing energy_limits as a tuple
            if 'plot' in user_dos_plot_config:
                if 'energy_limits' in user_dos_plot_config['plot']:
                    merged_config_dict['energy_limits'] = tuple(merged_config_dict['plot']['energy_limits'])
                if 'dos_limits' in user_dos_plot_config['plot']:
                    merged_config_dict['dos_limits'] = tuple(merged_config_dict['plot']['dos_limits'])
                del merged_config_dict['plot']

            # Extracting figure height and width from the merged 'figure' dictionary
            merged_config_dict['figure_height'] = merged_config_dict['figure']['height']
            merged_config_dict['figure_width'] = merged_config_dict['figure']['width']
            del merged_config_dict['figure']

            return cls(
                orbital_colors=merged_config_dict['orbital_colors'],
                figure_height=merged_config_dict['figure_height'],
                figure_width=merged_config_dict['figure_width'],
                energy_limits=merged_config_dict['energy_limits'],
                dos_limits=merged_config_dict['dos_limits']
            )

        except ConfigValidationError as e:
            print_error("An error occurred while validating the configuration file:")
            print_error(f"{str(e)}")
            print_warning("Using default configuration instead.")
            return cls.get_default_config()

        except FileNotFoundError:
            print_warning(f"Config file not found at `{config_file}`. Using defaults.")
            return cls.get_default_config()

    @classmethod
    def get_default_config(cls) -> 'DOSPlotConfig':
        """Creates configuration with default values."""
        return cls(
            orbital_colors={
                "s": "#FF00ED",
                "p": "#0BF317",
                "d": "#FF2B11",
                "all": "#FBFF2F"
            },
            figure_height=6,
            figure_width=12,
            energy_limits=(-5, 5),
            dos_limits=(0, 10)
        )