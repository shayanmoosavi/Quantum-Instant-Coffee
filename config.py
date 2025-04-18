"""Configuration management for the project.

This module provides functions to manage and load configuration settings
for the project. It supports loading configurations from a JSON file and
provides default settings if the file is not found.
"""

import json


def load_config(config_file="config.json"):
    """
    Load configuration from a JSON file.

    Args:
        config_file (str): Path to the configuration file. Defaults to "config.json".

    Returns:
        dict: The configuration settings loaded from the file. If the file is not found,
              the default configuration is returned.
    """
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_config()


def get_default_config():
    """
    Return default configuration settings.

    This function provides a fallback configuration in case the configuration
    file is not found. It defines the directory structure and file patterns
    used in the project.

    Returns:
        dict: A dictionary containing the default configuration settings.
    """
    return {
        "directory_structure": {
            "scf": "scf", # Directory for self-consistent field (SCF) calculations
            "scf_soc": "spin_orbit/scf", # Directory for spin-orbit SCF calculations
            "projected_bands": "projected_bands", # Directory for projected band data
            "projected_bands_soc": "spin_orbit/projected_bands", # Directory for spin-orbit projected bands
            "strain": "strain", # Directory for strain-related data
        },
        "file_patterns": {
            "bands_output": "{compound_name}_bands{flag}.pw.out", # Pattern for PW Band output files
            "kpdos_output": "{compound_name}{flag}.kpdos.out", # Pattern for KPDOS output files
            "projbands_output": "{compound_name}{flag}.projbands", # Pattern for generated projbands files from the AWK script
            "bands_gnu": "{compound_name}.bands.gnu", # Pattern for calculated band data
            "scf_output": "{compound_name}_scf{flag}.pw.out", # Pattern for SCF output files
        },
    }
