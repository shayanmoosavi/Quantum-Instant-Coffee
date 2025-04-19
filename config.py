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
            "wannier": "wannier", # Directory for Wannier calculations
            "wannier_soc": "spin_orbit/wannier", # Directory for spin-orbit Wannier calculations
            "strain": "strain", # Directory for strain-related data
        },
        "file_patterns": {
            "input": {
                "vc_relax_input": "{compound_name}_vc_relax{flag}.pw.in",  # Pattern for vc-relax input files
                "scf_input": "{compound_name}_scf{flag}.pw.in",  # Pattern for SCF input files
                "pw_bands_input": "{compound_name}_bands{flag}.pw.in",  # Pattern for PW Bands input files
                "kpdos_input": "{compound_name}{flag}.kpdos.in",  # Pattern for KPDOS input files
                "bands_input": "{compound_name}{flag}.bands.in",  # Pattern for Bands input files
                "nscf_wannier_input": "{compound_name}_nscf_wannier{flag}.pw.in",  # Pattern for NSCF wannier input files
                "pw2wan_input": "{compound_name}{flag}.pw2wan.in",  # Pattern for pw2wannier90 input files
                "wannier_input": "{compound_name}_wannier{flag}.win",  # Pattern for wannier input files
            },
            "output": {
                "vc_relax_output": "{compound_name}_vc_relax{flag}.pw.out",  # Pattern for vc-relax output files
                "scf_output": "{compound_name}_scf{flag}.pw.out",  # Pattern for SCF output files
                "pw_bands_output": "{compound_name}_bands{flag}.pw.out",  # Pattern for PW Bands output files
                "kpdos_output": "{compound_name}{flag}.kpdos.out",  # Pattern for KPDOS output files
                "projbands_output": "{compound_name}{flag}.projbands", # Pattern for generated projbands files from the AWK script
                "bands_gnu": "{compound_name}.bands.gnu",  # Pattern for calculated band data
            }
        },
    }
