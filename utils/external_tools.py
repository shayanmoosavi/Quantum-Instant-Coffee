""" Module for running external tools

This module provides utility functions for running external tools
such as AWK scripts and Quantum ESPRESSO's sumpdos.x.
"""
from subprocess import run
from typing import Tuple

from ui.ui_helpers import print_info


def run_awk_script(number_of_atomic_states: int,
                   fermi_energy: float,
                   kpdos_output_dir: str,
                   projbands_dir: str) -> None:
    """
    Execute the AWK script to generate projected bands data.

    Args:
        number_of_atomic_states (int): Number of atomic states
        fermi_energy (float): Fermi energy value
        kpdos_output_dir (str): KPDOS output path
        projbands_dir (str): Path to generate the projbands file

    Raises:
        CalledProcessError: If the AWK script execution fails
    """
    print_info("Calculating projected bands...")

    awk_command = (
        f"awk -v firststate=1 "
        f"-v laststate={number_of_atomic_states} "
        f"-v ef={fermi_energy} "
        f"-f utils/projwfc_to_bands.awk {kpdos_output_dir} > {projbands_dir}"
    )

    run(awk_command, shell=True, check=True, capture_output=True)


def run_sum_pdos(atomic_projection: Tuple[str, str]) -> None:
    """
    Executes the Quantum ESPRESSO sumpdos.x script to get the desired PDOS files.

    """

    print_info(f"Summing the PDOS files for {atomic_projection[0]}-{atomic_projection[1]}")

    sum_pdos_command = (f"sumpdos.x "
                        f"*\({atomic_projection[0]}\)*\({atomic_projection[1]}*\) "
                        f"> pdos_{atomic_projection[0]}_{atomic_projection[1]}.dat" if atomic_projection[1] != "all"
                        else f"sumpdos.x *\({atomic_projection[0]}\)* " 
                        f"> pdos_{atomic_projection[0]}_{atomic_projection[1]}.dat")

    run(sum_pdos_command, shell=True, check=True, capture_output=True)