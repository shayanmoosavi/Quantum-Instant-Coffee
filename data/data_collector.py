"""High-level module for collecting data from Quantum ESPRESSO output files.

This module provides functions for extracting and preparing data from Quantum ESPRESSO
output files, including band structure information, Wannier parameters, and PDOS data.

Functions:
    collect_band_numbers: Collects band numbers from Quantum ESPRESSO output files.
    collect_fermi_energies: Collects Fermi energies from Quantum ESPRESSO output files.
    collect_number_of_atomic_states: Collects the number of atomic states from KPDOS output files.
    collect_atomic_states_info: Collects atomic states information from KPDOS or PDOS output files.
    prepare_bands_info: Prepares band structure information by extracting data from output files.
    prepare_wannier_info: Prepares Wannier information by extracting data from NSCF Wannier output files.
    prepare_pdos_info: Prepares PDOS information by extracting data from output files.
"""
import argparse
from sys import argv
from typing import Any

from data.collector_factory import CollectionConfig, CollectorFactory
from data.data_generator import generate_pdos, generate_projected_bands
from ui.display_data import display_dft_info, display_atomic_states, display_wannier_info
from ui.ui_helpers import print_header
from utils.file_parser import *
from core.project_setup import initialize_project
from data.models import BandInfo, WannierSetup, ProjectSetup, DOSSetup
from core.project_setup import ProjectInitializationError


def collect_band_numbers(paths: Dict[str, List[str]],
                         compound_name: str,
                         spin_orbit_flags: List[str],
                         skip_soc: bool = False,
                         skip_normal: bool = False) -> list[int]:
    """
    Collect band numbers from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip SOC calculations
        skip_normal (bool): Whether to skip non-SOC calculations

    Returns:
        list: List of band numbers
    """
    config = CollectionConfig(
        paths=paths,
        compound_name=compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=skip_soc,
        skip_normal=skip_normal
    )

    collector = CollectorFactory.create_band_collector()
    return collector.collect(config)


def collect_fermi_energies(paths: Dict[str, List[str]],
                           compound_name: str,
                           spin_orbit_flags: List[str],
                           skip_soc: bool = False,
                           skip_normal: bool = False,
                           is_pdos: bool = False) -> List[float]:
    """
    Collect Fermi energies from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations
        skip_normal (bool): Whether to skip non-SOC calculations
        is_pdos (bool): Whether to collect Fermi energies from PDOS files

    Returns:
        list: List of Fermi energies
    """
    config = CollectionConfig(
        paths=paths,
        compound_name=compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=skip_soc,
        skip_normal=skip_normal,
        is_pdos=is_pdos
    )

    collector = CollectorFactory.create_fermi_collector()
    return collector.collect(config)


def collect_number_of_atomic_states(paths: Dict[str, List[str]],
                                    compound_name: str,
                                    spin_orbit_flags: List[str],
                                    skip_soc: bool = False,
                                    skip_normal: bool = False) -> List[int]:
    """
    Collect the number of atomic states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations
        skip_normal (bool): Whether to skip non-SOC calculations

    Returns:
        list: List of number of atomic states
    """
    config = CollectionConfig(
        paths=paths,
        compound_name=compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=skip_soc,
        skip_normal=skip_normal
    )

    collector = CollectorFactory.create_atomic_states_count_collector()
    return collector.collect(config)


def collect_atomic_states_info(paths: Dict[str, List[str]],
                               compound_name: str,
                               spin_orbit_flags: List[str],
                               skip_soc: bool = False,
                               skip_normal: bool = False,
                               is_pdos: bool = False) -> List[Dict[Any, Any]]:
    """
    Collect the atomic info states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flags (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations
        skip_normal (bool): Whether to skip non-SOC calculations
        is_pdos (bool): Whether to collect atomic states info from PDOS files

    Returns:
        list: A list of dictionaries containing the indices and orbital weights of each atomic state
    """
    config = CollectionConfig(
        paths=paths,
        compound_name=compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=skip_soc,
        skip_normal=skip_normal,
        is_pdos=is_pdos
    )

    collector = CollectorFactory.create_atomic_states_info_collector()
    return collector.collect(config)


def prepare_bands_info(project: ProjectSetup) -> ProjectSetup:
    """
    Prepare projected bands information by extracting data from Quantum ESPRESSO output files.

    Args:
        project (ProjectSetup): Project setup object containing paths and parameters.

    Returns:
        ProjectSetup: Updated project setup object with DFT information.
    """
    print_header("Bands Info Extraction")

    # Determine spin_orbit_flags based on project configuration
    spin_orbit_flags = (
        ["" for _ in range(len(project.stress_amounts) + 1)]
        if project.include_stress
        else ["", "_soc"]
    )

    # # Extracting band numbers
    number_of_bands_list = collect_band_numbers(
        project.output_paths,
        project.compound_name,
        spin_orbit_flags,
        project.skip_soc
    )

    # Extracting Fermi energies
    fermi_energies = collect_fermi_energies(
        project.output_paths,
        project.compound_name,
        spin_orbit_flags,
        project.skip_soc
    )

    # Extracting number of atomic states
    number_of_atomic_states_list = collect_number_of_atomic_states(
        project.output_paths,
        project.compound_name,
        spin_orbit_flags,
        project.skip_soc
    )

    # Extracting atomic states information
    atomic_states_info_list = collect_atomic_states_info(
        project.output_paths,
        project.compound_name,
        spin_orbit_flags,
        project.skip_soc
    )

    band_info = BandInfo(
        number_of_bands=number_of_bands_list,
        fermi_energies=fermi_energies,
        number_of_atomic_states=number_of_atomic_states_list,
        atomic_states_info=atomic_states_info_list,
        spin_orbit_flags=spin_orbit_flags
    )

    # Generate projected bands
    success = generate_projected_bands(
        project.output_paths,
        band_info.number_of_atomic_states,
        band_info.fermi_energies
    )

    if not all(success):
        raise ProjectInitializationError("Some projbands files were not generated successfully.")

    # Add DFT info to project
    project.add_bands_info(band_info)
    return project


def prepare_wannier_info(project: ProjectSetup) -> ProjectSetup:
    """Prepare Wannier information by extracting data from NSCF Wannier output files.

    Args:
        project (PojectSetup): Project setup object containing paths and parameters.

    Returns:
        WannierSetup: Configuration object for Wannier calculations

    Raises:
        ProjectInitializationError: If initialization fails
    """
    print_header("Wannier Info Extraction")

    spin_orbit_flags = ["", "_soc"]

    config = CollectionConfig(
        paths=project.output_paths,
        compound_name=project.compound_name,
        spin_orbit_flags=spin_orbit_flags,
        skip_soc=project.skip_soc,
        skip_normal=False
    )

    # Collect Wannier parameters using the factory pattern
    collector = CollectorFactory.create_wannier_collector()

    try:
        alat_parameters, fermi_energies = collector.collect(config)

        wannier_setup = WannierSetup(
            fermi_energies=fermi_energies,
            alat_parameters=alat_parameters,
            skip_normal=collector.soc_handler.skip_normal,
            skip_soc=collector.soc_handler.skip_soc
        )

        # Add Wannier setup to project configuration
        project.add_wannier_setup(wannier_setup)
        return project

    except Exception as e:
        raise ProjectInitializationError(f"Failed to prepare Wannier info: {str(e)}")


def prepare_pdos_info(project: ProjectSetup) -> ProjectSetup:
    """
    Prepare PDOS (Projected Density of States) information by extracting data from Quantum ESPRESSO output files.

    Args:
        project (ProjectSetup): Project setup object containing paths and parameters.

    Returns:
        ProjectSetup: Updated project setup object with PDOS information.
    """
    print_header("PDOS Info Extraction")

    spin_orbit_flags = ["", "_soc"]
    fermi_energies = collect_fermi_energies(project.output_paths,
                                            project.compound_name,
                                            spin_orbit_flags,
                                            project.skip_soc,
                                            is_pdos=True)

    atomic_states_info_list = collect_atomic_states_info(project.output_paths,
                                                         project.compound_name,
                                                         spin_orbit_flags,
                                                         project.skip_soc,
                                                         is_pdos=True)

    dos_setup = DOSSetup(fermi_energies=fermi_energies,
                         spin_orbit_flags=spin_orbit_flags,
                         atomic_states_info=atomic_states_info_list)

    project.add_dos_setup(dos_setup)

    success = generate_pdos(project.output_paths, list(project.dos_setup.atomic_states_info[0].keys()))
    if not all(success):
        raise ProjectInitializationError("Some PDOS files were not generated successfully.")

    return project


# Test to ensure the module works as expected
if __name__ == "__main__":
    """
    Main entry point for testing the module.

    This script validates that the prepare_dft_info has executed successfully and prints the extracted 
    information if successful.
    """
    os.chdir("..")

    # Create the parser
    parser = argparse.ArgumentParser(description="Tests the data collector module.")

    # Add arguments
    parser.add_argument(
        "compound_name",
        type=str,
        help="Name of the compound (e.g., 'GaAs', 'SiO2')."
    )

    parser.add_argument(
        "--project-config",
        type=str,
        help="Path to a custom JSON project configuration file."
    )

    parser.add_argument(
        "--config-type",
        type=str,
        default="bands",
        choices=["bands", "pdos", "wannier"],
        help="Type of configuration to use (default: 'bands')."
    )

    args = parser.parse_args(argv[1:])

    print_info(f"\n{args.config_type} config type was chosen for collecting data.")

    match args.config_type:
        case "wannier":
            project = initialize_project(args.compound_name,
                                         args.project_config,
                                         args.config_type,
                                         is_input=False, is_wannier=True)
            prepare_wannier_info(project)
            is_wannier = True
            is_pdos = False

        case "bands":
            project = initialize_project(args.compound_name,
                                         args.project_config,
                                         args.config_type,
                                         is_input=False)
            prepare_bands_info(project)
            is_wannier = False
            is_pdos = False

        case "pdos":
            project = initialize_project(args.compound_name,
                                         args.project_config,
                                         args.config_type,
                                         is_input=False, is_pdos=True)
            prepare_pdos_info(project)
            is_wannier = False
            is_pdos = True
        case _:
            print_error(f"Invalid configuration type: {args.config_type}")
            exit(1)

    print_info("Setup completed successfully.\n")

    if project.include_stress:
        print_header("Reporting Projected Bands Info")
        print('\n')
        for stress_amount, band, fermi_energy, states, atomic_states_info in zip(
                [None] + project.stress_amounts,
                project.band_info.number_of_bands,
                project.band_info.fermi_energies,
                project.band_info.number_of_atomic_states,
                project.band_info.atomic_states_info
        ):
            display_dft_info(band, fermi_energy, states, stress_amount)
    else:

        if not is_wannier and not is_pdos:
            print_header("Reporting Projected Bands Info")
            print('\n')
            for band, fermi_energy, states, atomic_states_info, flag in zip(
                    project.band_info.number_of_bands,
                    project.band_info.fermi_energies,
                    project.band_info.number_of_atomic_states,
                    project.band_info.atomic_states_info,
                    ["", "(SOC)"]
            ):
                console.rule(f"Info for {'Non-SOC' if flag == '' else 'SOC'} calculation")
                display_dft_info(band, fermi_energy, states)
                display_atomic_states(project.band_info.atomic_states_info[0])
                print('\n')

        elif is_pdos:
            print_header("Reporting PDOS Info")
            for fermi_energy, flag in zip(
                    project.dos_setup.fermi_energies,
                    ["", "(SOC)"]
            ):
                print_info(f"Fermi energy {flag}: {fermi_energy:.4f} eV")
        else:
            print_header("Reporting Wannier Info")
            print('\n')
            for fermi_energy, alat_parameter, flag in zip(
                    project.wannier_setup.fermi_energies,
                    project.wannier_setup.alat_parameters,
                    ["(SOC)"] if project.wannier_setup.skip_normal else ["", "(SOC)"]
            ):
                console.rule(f"Info for {'Non-SOC' if flag == '' else 'SOC'} calculation")
                display_wannier_info(fermi_energy, alat_parameter)
