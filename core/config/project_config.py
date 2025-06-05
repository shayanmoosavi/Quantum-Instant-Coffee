""" Module containing the ProjectConfig class for managing project configurations.

This module provides functionality to load, validate, and manage project configurations.
"""
import json
from dataclasses import dataclass
from typing import Dict

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
    def from_json(cls, config_file: str = "project_config.json", config_type: str = "default") -> 'ProjectConfig':
        """
        Load configuration from a JSON file and validate its structure.

        Args:
            config_file (str): Path to the JSON configuration file. Defaults to "project_config.json".
            config_type (str): Type of configuration to load. Defaults to "default".

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
            validate_config_structure(config_dict, config_type)

            return cls(
                directory_structure=config_dict['directory_structure'],
                file_patterns=FilePatterns(**config_dict['file_patterns'])
            )
        except FileNotFoundError:
            return cls.get_default_config(config_type)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON format in config file: {str(e)}")

    @classmethod
    def get_default_config(cls, config_type: str = "default") -> 'ProjectConfig':
        """
        Get the default configuration for the project.

        Args:
            config_type (str): Type of configuration to load. Defaults to "default".

        Returns:
            ProjectConfig: An instance of ProjectConfig with default settings.

        Raises:
            ConfigValidationError: If the default configuration structure is invalid.
        """
        match config_type:

            case "default":

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

            case "bands":

                config = cls(
                    directory_structure={
                        "scf": "scf",  # Directory for self-consistent field (SCF) calculations
                        "scf_soc": "spin_orbit/scf",  # Directory for spin-orbit SCF calculations
                        "projected_bands": "projected_bands",  # Directory for projected band data
                        "projected_bands_soc": "spin_orbit/projected_bands",  # Directory for spin-orbit projected bands
                        "pseudo": "../Pseudopotentials",  # Directory for pseudopotential files
                        "pseudo_rel": "../Pseudopotentials_rel"  # Directory for relativistic pseudopotential files
                    },
                    file_patterns=FilePatterns(
                        input={
                            "vc_relax_input": "{compound_name}_vc_relax{flag}.pw.in",  # Pattern for vc-relax input files
                            "scf_input": "{compound_name}_scf{flag}.pw.in",  # Pattern for SCF input files
                            "pw_bands_input": "{compound_name}_bands{flag}.pw.in",  # Pattern for PW Bands input files
                            "kpdos_input": "{compound_name}{flag}.kpdos.in",  # Pattern for KPDOS input files
                            "bands_input": "{compound_name}{flag}.bands.in"  # Pattern for Bands input files
                        },
                        output={
                            "vc_relax_output": "{compound_name}_vc_relax{flag}.pw.out",  # Pattern for vc-relax output files
                            "scf_output": "{compound_name}_scf{flag}.pw.out",  # Pattern for SCF output files
                            "pw_bands_output": "{compound_name}_bands{flag}.pw.out",  # Pattern for PW Bands output files
                            "kpdos_output": "{compound_name}{flag}.kpdos.out",  # Pattern for KPDOS output files
                            "projbands_output": "{compound_name}{flag}.projbands",
                            # Pattern for generated projbands files from the AWK script
                            "bands_gnu": "{compound_name}.bands.gnu"  # Pattern for DFT band data
                        }
                    )
                )

            case "pdos":

                config = cls(
                    directory_structure={
                        "scf": "scf",  # Directory for self-consistent field (SCF) calculations
                        "scf_soc": "spin_orbit/scf",  # Directory for spin-orbit SCF calculations
                        "pdos": "pdos",  # Directory for projected density of states (PDOS) calculations
                        "pdos_soc": "spin_orbit/pdos",  # Directory for spin-orbit PDOS calculations
                        "pseudo": "../Pseudopotentials",  # Directory for pseudopotential files
                        "pseudo_rel": "../Pseudopotentials_rel"  # Directory for relativistic pseudopotential files
                    },
                    file_patterns=FilePatterns(
                        input={
                            "vc_relax_input": "{compound_name}_vc_relax{flag}.pw.in",  # Pattern for vc-relax input files
                            "scf_input": "{compound_name}_scf{flag}.pw.in",  # Pattern for SCF input files
                            "nscf_input": "{compound_name}_nscf{flag}.pw.in",  # Pattern for NSCF input files
                            "pdos_input": "{compound_name}{flag}.pdos.in",  # Pattern for PDOS input files
                        },
                        output={
                            "vc_relax_output": "{compound_name}_vc_relax{flag}.pw.out",  # Pattern for vc-relax output files
                            "scf_output": "{compound_name}_scf{flag}.pw.out",  # Pattern for SCF output files
                            "nscf_output": "{compound_name}_nscf{flag}.pw.out",  # Pattern for NSCF output files
                            "pdos_output": "{compound_name}{flag}.pdos.out",  # Pattern for PDOS output files
                        }
                    )
                )

            case "wannier":

                config = cls(
                    directory_structure={
                        "scf": "scf",  # Directory for self-consistent field (SCF) calculations
                        "scf_soc": "spin_orbit/scf",  # Directory for spin-orbit SCF calculations
                        "wannier": "wannier",  # Directory for Wannier calculations
                        "wannier_soc": "spin_orbit/wannier",  # Directory for spin-orbit Wannier calculations
                        "projected_bands": "projected_bands",  # Directory for projected band data
                        "projected_bands_soc": "spin_orbit/projected_bands",  # Directory for spin-orbit projected bands
                        "pseudo": "../Pseudopotentials",  # Directory for pseudopotential files
                        "pseudo_rel": "../Pseudopotentials_rel"  # Directory for relativistic pseudopotential files
                    },
                    file_patterns=FilePatterns(
                        input={
                            "vc_relax_input": "{compound_name}_vc_relax{flag}.pw.in",  # Pattern for vc-relax input files
                            "scf_input": "{compound_name}_scf{flag}.pw.in",  # Pattern for SCF input files
                            "nscf_wannier_input": "{compound_name}_nscf_wannier{flag}.pw.in",
                            # Pattern for NSCF wannier input files
                            "pw2wan_input": "{compound_name}{flag}.pw2wan.in",  # Pattern for pw2wannier90 input files
                            "wannier_input": "{compound_name}_wannier{flag}.win",  # Pattern for wannier input files
                            "pw_bands_input": "{compound_name}_bands{flag}.pw.in",  # Pattern for PW Bands input files
                            "kpdos_input": "{compound_name}{flag}.kpdos.in",  # Pattern for KPDOS input files
                            "bands_input": "{compound_name}{flag}.bands.in"  # Pattern for Bands input files
                        },
                        output={
                            "vc_relax_output": "{compound_name}_vc_relax{flag}.pw.out",  # Pattern for vc-relax output files
                            "scf_output": "{compound_name}_scf{flag}.pw.out",  # Pattern for SCF output files
                            "nscf_wannier_output": "{compound_name}_nscf_wannier{flag}.pw.out",
                            # Pattern for NSCF wannier output files
                            "pw_bands_output": "{compound_name}_bands{flag}.pw.out",
                            # Pattern for PW Bands output files
                            "kpdos_output": "{compound_name}{flag}.kpdos.out",  # Pattern for KPDOS output files
                            "projbands_output": "{compound_name}{flag}.projbands",
                            # Pattern for generated projbands files from the AWK script
                            "bands_gnu": "{compound_name}.bands.gnu" , # Pattern for DFT band data
                            "wannier_bands": "{compound_name}_wannier{flag}_band.dat"  # Pattern for wannier band data
                        }
                    )
                )

            case _:
                raise ConfigValidationError("Invalid config_type. Must be 'default', 'bands', 'dos', or 'wannier'.")

        # Validate default configuration
        validate_config_structure({
            "directory_structure": config.directory_structure,
            "file_patterns": {
                "input": config.file_patterns.input,
                "output": config.file_patterns.output
            }
        }, config_type)

        return config