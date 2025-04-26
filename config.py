"""Configuration management for the project.

This module provides functions to manage and load configuration settings
for the project. It supports loading configurations from a JSON file and
provides default settings if the file is not found. It also validates the
configuration structure to ensure correctness.
"""

from dataclasses import dataclass
from typing import Dict
import json
from config_validation import validate_config_structure, ConfigValidationError


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
                "pseudo": "../Pseudopotentials", # Directory for pseudopotential files
                "pseudo_rel": "../Pseudopotentials_rel" # Directory for relativistic pseudopotential files
            },
            file_patterns=FilePatterns(
                input={
                    "relax_input": "{compound_name}_relax{flag}.pw.in",  # Pattern for relax input files
                    "vc_relax_input": "{compound_name}_vc_relax{flag}.pw.in", # Pattern for vc-relax input files
                    "scf_input": "{compound_name}_scf{flag}.pw.in",  # Pattern for SCF input files
                    "pw_bands_input": "{compound_name}_bands{flag}.pw.in",  # Pattern for PW Bands input files
                    "kpdos_input": "{compound_name}{flag}.kpdos.in",  # Pattern for KPDOS input files
                    "bands_input": "{compound_name}{flag}.bands.in",  # Pattern for Bands input files
                    "nscf_input": "{compound_name}_nscf{flag}.pw.in",  # Pattern for NSCF input files
                    "pdos_input": "{compound_name}{flag}.pdos.in",  # Pattern for PDOS input files
                    "nscf_wannier_input": "{compound_name}_nscf_wannier{flag}.pw.in", # Pattern for NSCF wannier input files
                    "pw2wan_input": "{compound_name}{flag}.pw2wan.in",  # Pattern for pw2wannier90 input files
                    "wannier_input": "{compound_name}_wannier{flag}.win",  # Pattern for wannier input files
                },
                output={
                    "relax_output": "{compound_name}_relax{flag}.pw.out",  # Pattern for relax output files
                    "vc_relax_output": "{compound_name}_vc_relax{flag}.pw.out",  # Pattern for vc-relax output files
                    "scf_output": "{compound_name}_scf{flag}.pw.out",  # Pattern for SCF output files
                    "pw_bands_output": "{compound_name}_bands{flag}.pw.out",  # Pattern for PW Bands output files
                    "kpdos_output": "{compound_name}{flag}.kpdos.out",  # Pattern for KPDOS output files
                    "projbands_output": "{compound_name}{flag}.projbands", # Pattern for generated projbands files from the AWK script
                    "bands_gnu": "{compound_name}.bands.gnu", # Pattern for calculated band data
                    "nscf_output": "{compound_name}_nscf{flag}.pw.out",  # Pattern for NSCF output files
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

def load_config(config_file: str = "config.json") -> ProjectConfig:
    """
    Load and validate the project configuration.

    Args:
        config_file (str): Path to the JSON configuration file. Defaults to "config.json".

    Returns:
        ProjectConfig: An instance of ProjectConfig with the loaded or default configuration.

    Raises:
        ConfigValidationError: If the configuration structure is invalid.
    """
    try:
        return ProjectConfig.from_json(config_file)
    except ConfigValidationError as e:
        print(f"Configuration validation error: {str(e)}")
        print("Using default configuration instead.")
        return ProjectConfig.get_default_config()
