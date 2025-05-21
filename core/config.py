"""Configuration management for the project.

This module provides functions to manage and load configuration settings
for the project. It supports loading configurations from a JSON file and
provides default settings if the file is not found. It also validates the
configuration structure to ensure correctness.
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json

from yaml import safe_load

from ui.ui_helpers import print_error, print_info, print_success, print_warning
from utils.config_validation import validate_config_structure, ConfigValidationError


@dataclass
class FilePatterns:
    """
    Represents file naming patterns for input and output files.

    Attributes:
        input (Dict[str, str]): A dictionary of input file patterns.
        output (Dict[str, str]): A dictionary of output file patterns.
    """
    input: Dict[str, str]
    output: Dict[str, str]


@dataclass
class ProjectConfig:
    """
    Represents the complete project configuration.

    Attributes:
        directory_structure (Dict[str, str]): A dictionary defining the directory structure.
        file_patterns (FilePatterns): An instance of FilePatterns containing input and output patterns.
    """
    directory_structure: Dict[str, str]
    file_patterns: FilePatterns

    @classmethod
    def from_json(cls, config_file: str = "config.json") -> 'ProjectConfig':
        """
        Load configuration from a JSON file and validate its structure.

        Args:
            config_file (str): Path to the JSON configuration file. Defaults to "config.json".

        Returns:
            ProjectConfig: An instance of ProjectConfig with the loaded configuration.

        Raises:
            ConfigValidationError: If the configuration structure is invalid.
            json.JSONDecodeError: If the JSON file is not properly formatted.
        """
        try:
            with open(config_file, "r") as f:
                config_dict = json.load(f)

            # Validate the loaded configuration
            validate_config_structure(config_dict)

            return cls(
                directory_structure=config_dict['directory_structure'],
                file_patterns=FilePatterns(**config_dict['file_patterns'])
            )
        except FileNotFoundError:
            return cls.get_default_config()
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON format in config file: {str(e)}")

    @classmethod
    def get_default_config(cls) -> 'ProjectConfig':
        """
        Get the default configuration for the project.

        Returns:
            ProjectConfig: An instance of ProjectConfig with default settings.

        Raises:
            ConfigValidationError: If the default configuration structure is invalid.
        """
        config = cls(
            directory_structure={
                "scf": "scf",  # Directory for self-consistent field (SCF) calculations
                "scf_soc": "spin_orbit/scf",  # Directory for spin-orbit SCF calculations
                "projected_bands": "projected_bands",  # Directory for projected band data
                "projected_bands_soc": "spin_orbit/projected_bands",  # Directory for spin-orbit projected bands
                "pdos": "pdos",  # Directory for projected density of states (PDOS) calculations
                "pdos_soc": "spin_orbit/pdos",  # Directory for spin-orbit PDOS calculations
                "wannier": "wannier",  # Directory for Wannier calculations
                "wannier_soc": "spin_orbit/wannier",  # Directory for spin-orbit Wannier calculations
                "strain": "strain",  # Directory for strain-related data
                "pseudo": "../Pseudopotentials",  # Directory for pseudopotential files
                "pseudo_rel": "../Pseudopotentials_rel"  # Directory for relativistic pseudopotential files
            },
            file_patterns=FilePatterns(
                input={
                    "relax_input": "{compound_name}_relax{flag}.pw.in",  # Pattern for relax input files
                    "vc_relax_input": "{compound_name}_vc_relax{flag}.pw.in",  # Pattern for vc-relax input files
                    "scf_input": "{compound_name}_scf{flag}.pw.in",  # Pattern for SCF input files
                    "pw_bands_input": "{compound_name}_bands{flag}.pw.in",  # Pattern for PW Bands input files
                    "kpdos_input": "{compound_name}{flag}.kpdos.in",  # Pattern for KPDOS input files
                    "bands_input": "{compound_name}{flag}.bands.in",  # Pattern for Bands input files
                    "nscf_input": "{compound_name}_nscf{flag}.pw.in",  # Pattern for NSCF input files
                    "pdos_input": "{compound_name}{flag}.pdos.in",  # Pattern for PDOS input files
                    "nscf_wannier_input": "{compound_name}_nscf_wannier{flag}.pw.in",
                    # Pattern for NSCF wannier input files
                    "pw2wan_input": "{compound_name}{flag}.pw2wan.in",  # Pattern for pw2wannier90 input files
                    "wannier_input": "{compound_name}_wannier{flag}.win",  # Pattern for wannier input files
                },
                output={
                    "relax_output": "{compound_name}_relax{flag}.pw.out",  # Pattern for relax output files
                    "vc_relax_output": "{compound_name}_vc_relax{flag}.pw.out",  # Pattern for vc-relax output files
                    "scf_output": "{compound_name}_scf{flag}.pw.out",  # Pattern for SCF output files
                    "pw_bands_output": "{compound_name}_bands{flag}.pw.out",  # Pattern for PW Bands output files
                    "kpdos_output": "{compound_name}{flag}.kpdos.out",  # Pattern for KPDOS output files
                    "projbands_output": "{compound_name}{flag}.projbands",
                    # Pattern for generated projbands files from the AWK script
                    "bands_gnu": "{compound_name}.bands.gnu",  # Pattern for DFT band data
                    "nscf_output": "{compound_name}_nscf{flag}.pw.out",  # Pattern for NSCF output files
                    "pdos_output": "{compound_name}{flag}.pdos.out",  # Pattern for PDOS output files
                    "nscf_wannier_output": "{compound_name}_nscf_wannier{flag}.pw.out",
                    # Pattern for NSCF wannier output files
                    "wannier_bands": "{compound_name}_wannier{flag}_band.dat"  # Pattern for wannier band data
                }
            )
        )

        # Validate default configuration
        validate_config_structure({
            "directory_structure": config.directory_structure,
            "file_patterns": {
                "input": config.file_patterns.input,
                "output": config.file_patterns.output
            }
        })

        return config


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
        try:

            with open(config_file, 'r') as f:
                config = safe_load(f)['bands_plot']

            return cls(
                high_symmetry_points=config['high_symmetry_points'],
                k_labels=[r"$\{}$".format(label) if label == "Gamma" else
                          r"${}$".format(label) for label in config['k_labels']],
                orbital_colors=config['orbital_colors'],
                figure_height=config['figure']['height'],
                figure_width=config['figure']['width'],
                energy_limits=tuple(config['figure']['energy_limits'])
            )
        except FileNotFoundError:
            print_warning(f"Config file not found at `{config_file}`. Using defaults.")
            return cls.get_default_config()

    @classmethod
    def get_default_config(cls) -> 'BandsPlotConfig':
        """Create configuration with default values."""
        plot_config = cls(
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
                "dx2y2+dxy": "#FF2B11"
            },
            figure_height=6,
            figure_width=12,
            energy_limits=(-5, 5)
        )
        return plot_config

@dataclass
class DOSPlotConfig:
    """Configuration class for PDOS plotting.

    Attributes:
        orbital_colors (dict): Color codes for different orbital types
        figure_height (int): Default figure height in inches
        figure_width (int): Default figure width in inches
        energy_limits (tuple): Y-axis energy range in eV
    """
    orbital_colors: Dict[str, str]
    figure_height: int
    figure_width: int
    energy_limits: Tuple

    @classmethod
    def from_yaml(cls, config_file: str = "plot_config.yaml") -> 'DOSPlotConfig':
        """Creates configuration from YAML file."""
        try:
            with open(config_file, 'r') as f:
                config = safe_load(f)['dos_plot']

            return cls(
                orbital_colors=config['orbital_colors'],
                figure_height=config['figure']['height'],
                figure_width=config['figure']['width'],
                energy_limits=tuple(config['figure']['energy_limits'])
            )
        except FileNotFoundError:
            print_warning(f"Config file not found at `{config_file}`. Using defaults.")
            return cls.get_default_config()

    @classmethod
    def get_default_config(cls) -> 'DOSPlotConfig':
        """Creates configuration with default values."""
        return cls(
            orbital_colors= {
                "s": "#FF00ED",
                "p": "#0BF317",
                "d": "#FF2B11"
            },
        figure_height = 6,
        figure_width= 12,
        energy_limits = (-5, 5)
        )


def load_config(config_file: str = None,
                config_type: str = "project") -> ProjectConfig | BandsPlotConfig | DOSPlotConfig:
    """
    Load and validate the project configuration.

    Args:
        config_file (str): Path to the JSON configuration file. Defaults to None.
        config_type (str): Type of configuration to load. Defaults to 'project'

    Returns:
        ProjectConfig: An instance of ProjectConfig with the loaded or default configuration.

    Raises:
        ConfigValidationError: If the configuration structure is invalid.
    """
    if config_type not in ("project", "bands", "dos"):
        raise ValueError("Invalid config_type. Must be 'project', 'bands', or 'dos'.")

    is_project_config = config_type == "project"
    try:
        if not config_file:
            print_info("Loading project configuration file...") if is_project_config \
                else print_info("Loading plot configuration file...")
            user_id = os.getenv("COFFEE")
            if user_id:
                script_root_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), ".."))  # The root directory of the program
                config_file = os.path.join(script_root_dir, "..", user_id, "config.json" if is_project_config else "plot_config.yaml")
                print_info(f"Config file path: {os.path.abspath(config_file)}")
                if os.path.exists(os.path.abspath(config_file)):
                    print_success(f"Config found for {user_id}")
                else:
                    print_warning(f"Config not found for {user_id}")
                    print_info("Using default configuration instead.")
                    config_file = "config.json" if is_project_config else "plot_config.yaml"
            else:
                print_warning("Environment variable 'COFFEE' not set. Using default configuration.")
                config_file = "config.json" if is_project_config else "plot_config.yaml"

        match config_type:
            case "project":
                return ProjectConfig.from_json(config_file)
            case "bands":
                return BandsPlotConfig.from_yaml(config_file)
            case "dos":
                return DOSPlotConfig.from_yaml(config_file)
            case _:
                raise ValueError("Invalid config_type. Must be 'project', 'bands', or 'dos'.")

    except ValueError as e:
        raise ConfigValidationError(f"Error in loading config file: {str(e)}")

    except ConfigValidationError as e:
        print_error(f"Configuration validation error: {str(e)}")
        print_info("Using default configuration instead.")

        match config_type:
            case "project":
                return ProjectConfig.get_default_config()
            case "bands":
                return BandsPlotConfig.get_default_config()
            case "dos":
                return DOSPlotConfig.get_default_config()
            case _:
                raise ValueError("Invalid config_type. Must be 'project', 'bands', or 'dos'.")