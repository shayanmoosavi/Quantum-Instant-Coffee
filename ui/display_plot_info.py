""" Module for displaying debug information for plots in Quantum Instant Coffee.

It includes functions to format and print debug information for band structure plots,
Wannier comparison plots, and projected density of states (PDOS) plots.
These functions utilize the `rich` library to create formatted tables for displaying
the information in a user-friendly manner.
"""
from typing import Dict, List

from rich import box
from rich.table import Table

from ui.ui_helpers import console


def display_band_plot_info(projection_info: Dict,
                           spin_orbit_flag: str,
                           include_stress: bool = False,
                           stress_amount: str = None):
    """
    Display debug information for band structure plots in a formatted table.

    Args:
        projection_info (Dict): Dictionary containing projection data for each element.
        spin_orbit_flag (str): Flag indicating whether spin-orbit coupling (SOC) is enabled.
        include_stress (bool, optional): Whether to include stress information in the table. Defaults to False.
        stress_amount (str, optional): Stress amount as a string (e.g., '1_30'). Defaults to None.
    """
    # Creating a table with a title and rounded box style
    debug_table = Table(title="Projection Info Debug", box=box.ROUNDED)
    debug_table.add_column("Parameter", style="cyan")
    debug_table.add_column("Value", style="green")

    # Add strain information if stress is included, otherwise add SOC status
    if include_stress:
        strain = float(stress_amount.replace('_', '.')) * 100
        debug_table.add_row("Strain", f"{strain:.2f}%")
    else:
        debug_table.add_row("SOC", "Yes" if spin_orbit_flag else "No")

    # Add rows for each element's projection data, excluding orbital weights
    for atom, info in projection_info.items():
        debug_info = {k: v for k, v in info.items() if k != "orbital_weights"}
        debug_table.add_row(f"Element {atom}", str(debug_info))

    console.print(debug_table)


def display_wannier_plot_info(fermi_energy: float, alat: float, flag: str):
    """
    Display debug information for Wannier comparison plots in a formatted table.

    Args:
        fermi_energy (float): Fermi energy value in eV.
        alat (float): Lattice parameter in Å.
        flag (str): Spin-orbit coupling (SOC) flag (e.g., '_soc').
    """
    # Creating a table with a title and rounded box style
    debug_table = Table(box=box.ROUNDED, title="Wannier Comparison Debug Info")
    debug_table.add_column("Parameter", style="cyan")
    debug_table.add_column("Value", style="green")

    debug_table.add_row("Fermi Energy (eV)", f"{fermi_energy:.4f}")
    debug_table.add_row("Alat (Å)", f"{alat:.6f}")
    debug_table.add_row("SOC Flag", "Yes" if flag == "_soc" else "No")

    console.print(debug_table)


def display_pdos_plot_info(elements: List[str], projection_data: Dict[str, Dict]):
    """
    Display debug information for projected density of states (PDOS) plots in a formatted table.

    Args:
        elements (List[str]): List of unique chemical elements.
        projection_data (Dict[str, Dict]): Dictionary containing projection data for each element.
    """
    # Creating a table with a title and rounded box style
    debug_table = Table(box=box.ROUNDED, title="PDOS Debug Info")
    debug_table.add_column("Parameter", style="cyan")
    debug_table.add_column("Value", style="green")

    debug_table.add_row("Elements", ", ".join(elements))

    for element, data in projection_data.items():
        element_info = {
            "index": data["index"],
            "projected_orbitals": data["projected_orbitals"],
            "plot_colors": data["plot_colors"]
        }
        debug_table.add_row(f"Element {element}", str(element_info))

    console.print(debug_table)