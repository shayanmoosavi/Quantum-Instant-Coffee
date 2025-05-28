"""
Module for displaying data

This module provides functions to display various types of data in a formatted manner using the Rich library.
"""

from typing import Dict, Any

from numpy import ndarray
from rich import box
from rich.table import Table

from ui.ui_helpers import console


def display_dft_info(band: int, fermi_energy: float, states: int, stress_amount: str | None = None) -> None:
    """
    Display DFT (Density Functional Theory) calculation information in a formatted table.

    Args:
        band (int): The number of bands in the calculation.
        fermi_energy (float): The Fermi energy value in eV.
        states (int): The number of atomic states.
        stress_amount (str | None): The stress amount in the format '1_<percent>' (e.g., '1_30')
                                    or None if no stress is applied.

    Returns:
        None: This function prints the DFT calculation information to the console.
    """
    table = Table(box=box.ROUNDED, title="DFT Calculation Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    if stress_amount:
        strain_percent = float(stress_amount.replace('_', '.')) * 100
        table.caption = f"Results for {strain_percent:.2f}% strain"

    # Add rows for each property
    table.add_row("Number of bands", str(band))
    table.add_row("Fermi energy (eV)", f"{fermi_energy:.4f}")
    table.add_row("Atomic states", str(states))

    console.print(table)


def display_atomic_states(atomic_states_info: Dict[str, Any]) -> None:
    """
    Display atomic states information in a formatted table.

    Args:
        atomic_states_info (Dict[str, Any]): A dictionary containing atomic states and their properties.

    Returns:
        None: This function prints the atomic states information to the console.
    """
    table = Table(title="Atomic States Info", box=box.ROUNDED)
    table.add_column("State", style="cyan")
    table.add_column("Properties", style="green")

    for state, info in atomic_states_info.items():
        table.add_row(state, str(info))

    console.print(table)


def display_wannier_info(fermi_energy: float, alat_parameter: float) -> None:
    """
    Display Wannier calculation information in a formatted table.

    Args:
        fermi_energy (float): The Fermi energy value in eV.
        alat_parameter (float): The lattice parameter in Ångströms.

    Returns:
        None: This function prints the Wannier calculation information to the console.
    """
    table = Table(title="Wannier Info", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Fermi energy (eV)", f"{fermi_energy:.4f}")
    table.add_row("Lattice parameter (Å)", f"{alat_parameter:.6f}")

    console.print(table)


def display_dft_data_info(bands: int, kpoints: ndarray, fermi_energy: float, stress_amount: str = None):
    table = Table(title="Bands Info", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    if stress_amount:
        strain_percent = float(stress_amount.replace('_', '.')) * 100
        table.caption = f"Results for {strain_percent:.2f}% strain"

    table.add_row("Number of bands", str(bands))
    table.add_row("Number of k-points", str(len(kpoints)))
    table.add_row("Fermi energy (eV)", f"{fermi_energy:.4f}")

    console.print(table)