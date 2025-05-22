"""
This module provides functions to validate the configuration structure for the project.
It ensures that the directory structure and file patterns are correctly defined and meet
the required specifications.

Classes:
    ConfigValidationError: Custom exception raised when configuration validation fails.

Functions:
    validate_directory_structure(directory_structure): Validates the directory structure configuration.
    validate_file_patterns(patterns): Validates the file pattern configuration.
    validate_config_structure(config): Validates the overall configuration structure.
"""

from typing import Dict, Any

class ConfigValidationError(Exception):
    """
    Custom exception raised when configuration validation fails.

    Attributes:
        message (str): Explanation of the validation error.
    """
    pass

def validate_directory_structure(directory_structure: Dict[str, str]) -> None:
    """
    Validate the directory structure configuration.

    Args:
        directory_structure (Dict[str, str]): A dictionary where keys are directory names
            and values are their corresponding paths.

    Raises:
        ConfigValidationError: If required directories are missing or if any path is not a string.
    """
    required_dirs = {
        "scf",
        "scf_soc",
        "projected_bands",
        "projected_bands_soc",
        "pseudo",
        "pseudo_rel"
    }

    # Check for missing required directories
    if missing := required_dirs - set(directory_structure.keys()):
        raise ConfigValidationError(f"Missing required directory entries: {missing}")

    # Ensure all directory paths are strings
    if not all(isinstance(path, str) for path in directory_structure.values()):
        raise ConfigValidationError("All directory paths must be strings")

def validate_file_patterns(patterns: Dict[str, Dict[str, str]]) -> None:
    """
    Validate the file pattern configuration.

    Args:
        patterns (Dict[str, Dict[str, str]]): A dictionary containing input and output file patterns.

    Raises:
        ConfigValidationError: If required patterns are missing, if any pattern is not a string,
            or if required placeholders are missing in the patterns.
    """
    required_patterns = {
        "input": {
            "vc_relax_input",
            "scf_input",
            "pw_bands_input",
            "kpdos_input",
            "bands_input",
        },
        "output": {
            "vc_relax_output",
            "scf_output",
            "pw_bands_output",
            "kpdos_output",
            "projbands_output",
            "bands_gnu"
        }
    }

    # Validate input and output patterns
    for pattern_type in ("input", "output"):
        if pattern_type not in patterns:
            raise ConfigValidationError(f"Missing {pattern_type} patterns section")

        # Check for missing required patterns
        if missing := required_patterns[pattern_type] - set(patterns[pattern_type].keys()):
            raise ConfigValidationError(f"Missing required {pattern_type} patterns: {missing}")

        # Validate each pattern's format
        for pattern_name, pattern in patterns[pattern_type].items():
            if not isinstance(pattern, str):
                raise ConfigValidationError(f"Pattern {pattern_name} must be a string")
            if "{compound_name}" not in pattern:
                raise ConfigValidationError(f"Pattern {pattern_name} must contain {{compound_name}} placeholder")
            if "{flag}" not in pattern and pattern_name != "bands_gnu":
                raise ConfigValidationError(f"Pattern {pattern_name} must contain {{flag}} placeholder")

def validate_config_structure(config: Dict[str, Any]) -> None:
    """
    Validate the overall configuration structure.

    Args:
        config (Dict[str, Any]): The complete configuration dictionary.

    Raises:
        ConfigValidationError: If required sections are missing or if any section fails validation.
    """
    required_sections = {"directory_structure", "file_patterns"}

    # Check for missing required sections
    if missing := required_sections - set(config.keys()):
        raise ConfigValidationError(f"Missing required configuration sections: {missing}")

    # Validate individual sections
    validate_directory_structure(config["directory_structure"])
    validate_file_patterns(config["file_patterns"])


def validate_plot_config_structure(config: Dict[str, Any], config_type: str) -> None:
    """
    Validate plot configuration structure.

    Args:
        config: Configuration dictionary to validate
        config_type: Type of config ('bands' or 'dos')

    Raises:
        ConfigValidationError: If validation fails
    """
    required_sections = {
        'bands': 'bands_plot',
        'dos': 'dos_plot'
    }

    section_name = required_sections[config_type]

    if section_name not in config:
        raise ConfigValidationError(f"Missing required section: {section_name}")

    section_config = config[section_name]

    def validate_sections(section_config: Dict[str, Any], config_type: str = "bands"):
        """
        Validates sections of the plot configuration.

        Args:
            section_config: Configuration dictionary for the specific section
            config_type: Type of config ('bands' or 'dos')

        Raises:
            ConfigValidationError: If validation fails
        """
        if 'orbital_colors' in section_config:
            if not isinstance(section_config['orbital_colors'], dict):
                raise ConfigValidationError(
                    "Invalid orbital_colors section! Check default plot_config.yaml to see the correct format.")

        if 'figure' in section_config:
            figure_config = section_config['figure']
            if not isinstance(figure_config, dict):
                raise ConfigValidationError(
                    "Invalid figure section! Check default plot_config.yaml to see the correct format.")

            # Validate numeric fields if present
            for field in ['height', 'width']:
                if field in figure_config and not isinstance(figure_config[field], (int, float)):
                    raise ConfigValidationError(f"figure.{field} must be numeric")

            if 'energy_limits' in figure_config:
                energy_limits = figure_config['energy_limits']

                if not isinstance(energy_limits, list) or len(energy_limits) != 2:
                    raise ConfigValidationError(
                        "figure.energy_limits must be a list of two numeric values.")

                if not all(isinstance(val, (int, float)) for val in energy_limits):
                    raise ConfigValidationError(
                        "figure.energy_limits must be a list of two numeric values.")

        if config_type == 'bands':
            if 'high_symmetry_points' in section_config:
                high_symmetry_points = section_config['high_symmetry_points']
                if not isinstance(high_symmetry_points, list):
                    raise ConfigValidationError(
                        "high_symmetry_points section must be a list of floats.")
                else:
                    for point in high_symmetry_points:
                        if not isinstance(point, float):
                            raise ConfigValidationError(
                                "high_symmetry_points section must be a list of floats.")

            if 'k_labels' in section_config:
                k_labels = section_config['k_labels']
                if not isinstance(k_labels, list):
                    raise ConfigValidationError(
                        "k_labels section must be a list of strings.")
                else:
                    for label in k_labels:
                        if not isinstance(label, str):
                            raise ConfigValidationError(
                                "k_labels section must be a list of strings.")

    # Validate based on config type
    if config_type == 'bands':
        validate_sections(section_config, config_type="bands")

    elif config_type == 'dos':
        validate_sections(section_config, config_type="dos")