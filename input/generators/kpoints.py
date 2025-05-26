from subprocess import run, CalledProcessError
from typing import Tuple

from input.generators.sections import InputGenerationError


def generate_k_points_section(calculation_type: str,
                              k_mesh_density: Tuple[int, int, int] = None,
                              is_wannier=False) -> str | None:
    """
    Generates the K_POINTS section of the input files for Quantum ESPRESSO or
    kpoints section of Wannier90 input file.

    Args:
        calculation_type (str): The calculation type (e.g., 'scf', 'bands').
        k_mesh_density (tuple): The K-point mesh density.
        is_wannier (bool): Whether the calculation is for Wannier case

    Returns:
        str: The K_POINTS section of the input file.

    Raises:
        InputGenerationError: If the calculation type is invalid or k_mesh_density is not provided.
    """
    valid_calc_types = ("relax", "vc-relax", "scf", "bands", "nscf", "wannier")

    if calculation_type not in valid_calc_types:
        raise InputGenerationError(f"Invalid calculation type: {calculation_type}. "
                                   f"Valid types are: {', '.join(valid_calc_types)}")

    try:
        if len(k_mesh_density) != 3:
            raise ValueError("k_mesh_density must be three integers separated by spaces.")

    except TypeError:
        if calculation_type != "bands":
            raise InputGenerationError(f"K-point mesh density cannot be None for {calculation_type} calculation.")

    if calculation_type in ["relax", "vc-relax", "scf"]:
        k_points_section = "K_POINTS automatic\n"
        k_points_section += f" {k_mesh_density[0]} {k_mesh_density[1]} {k_mesh_density[2]} 0 0 0\n"

        return k_points_section

    elif calculation_type == "nscf":
        if is_wannier:
            try:
                k_points_section = run(f"utils/kmesh.pl {k_mesh_density[0]} {k_mesh_density[1]} {k_mesh_density[2]}",
                                       shell=True, check=True, capture_output=True).stdout.decode("utf-8")
                return k_points_section
            except CalledProcessError as e:
                raise InputGenerationError(
                    f"An error occurred in running kmesh.pl script:\n {e.stderr.decode('utf-8')}")

        else:
            k_points_section = "K_POINTS automatic\n"
            k_points_section += f" {k_mesh_density[0]} {k_mesh_density[1]} {k_mesh_density[2]} 0 0 0\n"

            return k_points_section

    elif calculation_type == "wannier":
        try:
            k_points_section = run(f"utils/kmesh.pl {k_mesh_density[0]} {k_mesh_density[1]} {k_mesh_density[2]} wann",
                                   shell=True, check=True, capture_output=True).stdout.decode("utf-8")
            return k_points_section
        except CalledProcessError as e:
            raise InputGenerationError(f"An error occurred in running kmesh.pl script:\n {e.stderr.decode('utf-8')}")

    elif calculation_type == "bands":
        k_points_section = """K_POINTS crystal_b
4
0.0000000000    0.0000000000    0.0000000000    120 ! Gamma
0.5000000000    0.0000000000    0.0000000000    120 ! M
0.3333333333    0.3333333333    0.0000000000    120 ! K
0.0000000000    0.0000000000    0.0000000000      0 ! Gamma
"""
        return k_points_section

    else:
        raise InputGenerationError(f"Unsupported calculation type: {calculation_type}. "
                                   f"Valid types are: {', '.join(valid_calc_types)}")