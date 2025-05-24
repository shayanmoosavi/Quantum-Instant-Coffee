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


def validate_directory_structure(directory_structure: Dict[str, str],
                                 directory_structure_config: str = "default") -> None:
    """
    Validate the directory structure configuration.

    Args:
        directory_structure (Dict[str, str]): A dictionary where keys are directory names
            and values are their corresponding paths.
        directory_structure_config (str): Type of directory structure config, either 'default',
        'bands', 'dos', or 'wannier'. 'default' is the scf, projected_bands, and pdos directories
        while the rest only contain scf with their respective directory types.

    Raises:
        ConfigValidationError: If required directories are missing or if any path is not a string.
    """
    match directory_structure_config:

        case "default":
            # Base required directories (always mandatory)
            base_required_dirs = {
                "scf",
                "projected_bands",
                "pdos",
                "pseudo"
            }

            # SOC-related directories (all or none must be present)
            soc_dirs = {
                "scf_soc",
                "projected_bands_soc",
                "pdos_soc",
                "pseudo_rel"
            }

        case "bands":
            # Base required directories (always mandatory)
            base_required_dirs = {
                "scf",
                "projected_bands",
                "pseudo"
            }

            # SOC-related directories (all or none must be present)
            soc_dirs = {
                "scf_soc",
                "projected_bands_soc",
                "pseudo_rel"
            }

        case "pdos":
            # Base required directories (always mandatory)
            base_required_dirs = {
                "scf",
                "pdos",
                "pseudo"
            }

            # SOC-related directories (all or none must be present)
            soc_dirs = {
                "scf_soc",
                "pdos_soc",
                "pseudo_rel"
            }

        case "wannier":
            # Base required directories (always mandatory)
            base_required_dirs = {
                "scf",
                "wannier",
                "pseudo"
            }

            # SOC-related directories (all or none must be present)
            soc_dirs = {
                "scf_soc",
                "wannier_soc",
                "pseudo_rel"
            }
        case _:
            raise ConfigValidationError(
                f"Invalid config type: {directory_structure_config}. Valid types are 'default', 'bands', 'dos', or 'wannier'.")

    # Check for missing required directories
    if missing := base_required_dirs - set(directory_structure.keys()):
        raise ConfigValidationError(f"Missing required directory entries: {missing}")

    # Check SOC directories - if any are present, all must be present
    present_soc_dirs = soc_dirs & set(directory_structure.keys())
    if present_soc_dirs and present_soc_dirs != soc_dirs:
        missing_soc_dirs = soc_dirs - present_soc_dirs
        raise ConfigValidationError(
            f"When SOC directories are used, all SOC directories must be present. "
            f"Missing SOC directories: {missing_soc_dirs}. "
            f"Present SOC directories: {present_soc_dirs}"
        )

    # Ensure all directory paths are strings
    if not all(isinstance(path, str) for path in directory_structure.values()):
        raise ConfigValidationError("All directory paths must be strings")


def validate_file_patterns(patterns: Dict[str, Dict[str, str]], patterns_config: str = "default") -> None:
    """
    Validate the file pattern configuration.

    Args:
        patterns (Dict[str, Dict[str, str]]): A dictionary containing input and output file patterns.
        patterns_config (str): Type of patterns config, either 'default', 'bands', 'dos', or 'wannier'. 'default' is the
        vc_relax, scf, projected_bands, and pdos file patterns while the rest only contain scf with their respective file patterns.

    Raises:
        ConfigValidationError: If required patterns are missing, if any pattern is not a string,
            or if required placeholders are missing in the patterns.
    """
    match patterns_config:

        case "default":
            required_patterns = {
                "input": {
                    "vc_relax_input",
                    "scf_input",
                    "pw_bands_input",
                    "kpdos_input",
                    "bands_input",
                    "nscf_input",
                    "pdos_input"
                },
                "output": {
                    "vc_relax_output",
                    "scf_output",
                    "pw_bands_output",
                    "kpdos_output",
                    "projbands_output",
                    "nscf_output",
                    "pdos_output"
                }
            }

        case "bands":
            required_patterns = {
                "input": {
                    "scf_input",
                    "pw_bands_input",
                    "kpdos_input",
                    "bands_input"
                },
                "output": {
                    "scf_output",
                    "pw_bands_output",
                    "kpdos_output",
                    "projbands_output",
                    "bands_gnu"
                }
            }

        case "pdos":
            required_patterns = {
                "input": {
                    "scf_input",
                    "nscf_input",
                    "pdos_input"
                },
                "output": {
                    "scf_output",
                    "nscf_output",
                    "pdos_output"
                }
            }

        case "wannier":
            required_patterns = {
                "input": {
                    "scf_input",
                    "nscf_wannier_input",
                    "pw2wan_input",
                    "wannier_input"
                },
                "output": {
                    "scf_output",
                    "nscf_wannier_output",
                    "wannier_bands"
                }
            }

        case _:
            raise ConfigValidationError(
                f"Invalid config type: {patterns_config}. Valid types are 'default', 'bands', 'dos', or 'wannier'.")

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


def validate_config_structure(config: Dict[str, Any], project_config_type: str = "default") -> None:
    """
    Validate the overall configuration structure.

    Args:
        config (Dict[str, Any]): The complete configuration dictionary.
        project_config_type (str): Type of config, either 'default', 'bands', 'dos', or 'wannier'.

    Raises:
        ConfigValidationError: If required sections are missing or if any section fails validation.
    """
    required_sections = {"directory_structure", "file_patterns"}

    # Check for missing required sections
    if missing := required_sections - set(config.keys()):
        raise ConfigValidationError(f"Missing required configuration sections: {missing}")

    # Validate individual sections
    validate_directory_structure(config["directory_structure"], project_config_type)
    validate_file_patterns(config["file_patterns"], project_config_type)


def validate_plot_config_structure(config: Dict[str, Any], plot_config_type: str) -> None:
    """
    Validate plot configuration structure.

    Args:
        config: Configuration dictionary to validate
        plot_config_type: Type of config ('bands' or 'dos')

    Raises:
        ConfigValidationError: If validation fails
    """
    required_sections = {
        "bands": "bands_plot",
        "dos": "dos_plot"
    }

    section_name = required_sections[plot_config_type]

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
        if "orbital_colors" in section_config:
            if not isinstance(section_config["orbital_colors"], dict):
                raise ConfigValidationError(
                    "Invalid orbital_colors section! Check default plot_config.yaml to see the correct format.")

        if "figure" in section_config:
            figure_config = section_config["figure"]
            if not isinstance(figure_config, dict):
                raise ConfigValidationError(
                    "Invalid figure section! Check default plot_config.yaml to see the correct format.")

            # Validate numeric fields if present
            for field in ["height", "width"]:
                if field in figure_config and not isinstance(figure_config[field], (int, float)):
                    raise ConfigValidationError(f"figure.{field} must be numeric")

            if "energy_limits" in figure_config:
                energy_limits = figure_config["energy_limits"]

                if not isinstance(energy_limits, list) or len(energy_limits) != 2:
                    raise ConfigValidationError(
                        "figure.energy_limits must be a list of two numeric values.")

                if not all(isinstance(val, (int, float)) for val in energy_limits):
                    raise ConfigValidationError(
                        "figure.energy_limits must be a list of two numeric values.")

        if config_type == "bands":
            if "high_symmetry_points" in section_config:
                high_symmetry_points = section_config["high_symmetry_points"]
                if not isinstance(high_symmetry_points, list):
                    raise ConfigValidationError(
                        "high_symmetry_points section must be a list of floats.")
                else:
                    for point in high_symmetry_points:
                        if not isinstance(point, float):
                            raise ConfigValidationError(
                                "high_symmetry_points section must be a list of floats.")

            if "k_labels" in section_config:
                k_labels = section_config["k_labels"]
                if not isinstance(k_labels, list):
                    raise ConfigValidationError(
                        "k_labels section must be a list of strings.")
                else:
                    for label in k_labels:
                        if not isinstance(label, str):
                            raise ConfigValidationError(
                                "k_labels section must be a list of strings.")

    # Validate based on config type
    if plot_config_type == "bands":
        validate_sections(section_config, config_type="bands")

    elif plot_config_type == "pdos":
        validate_sections(section_config, config_type="pdos")
