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