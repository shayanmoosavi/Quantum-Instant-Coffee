import os
from subprocess import CalledProcessError
from typing import Dict, List

from ui.ui_helpers import print_header, console, print_warning, print_success, print_error, print_info
from utils.external_tools import run_awk_script, run_sum_pdos


def generate_projected_bands(paths: Dict[str, List[str]],
                             number_of_atomic_states_list: List[int],
                             fermi_energies: List[float]) -> List[bool]:
    """
    Generate projected bands data if not already present.

    This function checks if the projected bands file already exists. If it does not,
    it runs an AWK script to generate the file. The function tracks the success or
    failure of the generation process for each file.

    Args:
        paths (dict): A dictionary containing file paths, including:
            - "kpdos_output_paths" (list): List of KPDOS output file paths.
            - "projbands_paths" (list): List of paths where projbands files should be generated.
        number_of_atomic_states_list (list): A list of integers representing the number of atomic states for each calculation output
        fermi_energies (list): A list of floats representing the Fermi energy values for each calculation output.
    Returns:
        list: A list of boolean values indicating the success (True) or failure (False)
              of the projected bands generation for each file.
    """
    print_header("Generating Projected Bands Data")

    # List to track whether the projbands generation was successful for each file
    success_list = []

    # Iterating over the KPDOS output paths and corresponding projbands paths
    for i, (projbands_dir, kpdos_output_dir,
            number_of_atomic_states, fermi_energy) in enumerate(zip(
        paths["projbands_paths"], paths["kpdos_output_paths"],
        number_of_atomic_states_list, fermi_energies
    )):
        console.rule(f"Generating file {i + 1} of {len(paths['projbands_paths'])}")

        # Checking if the projbands file already exists
        if os.path.exists(projbands_dir):
            print_warning(f"File already exists: `{os.path.basename(projbands_dir)}`\n")
            success_list.append(True)
            continue

        try:
            with console.status("Calculating projected bands..."):

                # Running the AWK script to generate the projbands file
                run_awk_script(number_of_atomic_states, fermi_energy, kpdos_output_dir, projbands_dir)

            print_success(f"Created: `{os.path.basename(projbands_dir)}`\n")
            success_list.append(True)

        except CalledProcessError as e:

            # Handling errors during the AWK script execution
            print_error(f"Failed to generate: `{os.path.basename(projbands_dir)}`")
            print_error(e.stderr.decode("utf-8"))
            success_list.append(False)

    return success_list


def generate_pdos(paths: Dict[str, List[str]],
                  atomic_projection_list: List[str],
                  skip_soc: bool = False,
                  skip_normal: bool = False
                  ) -> List[bool]:
    """
    Generates Projected Density of States (PDOS) files if not already present.

    Args:
        paths (Dict[str, List[str]]): Dictionary containing output file paths
        atomic_projection_list (List[str]): List of atomic projections in "atom-orbital" format

    Returns:
        List[bool]: List of boolean values indicating success/failure for each file generation
    """
    print_header("Generating PDOS Data")

    # List to track whether the pdos generation was successful for each file
    success_list = []

    total_files = len(atomic_projection_list) if skip_soc or skip_normal else len(paths["pdos_output_paths"]) * len(
        atomic_projection_list)
    current_file = 0

    # Iterating over the PDOS output paths and corresponding PDOS data
    for pdos_dir in paths["pdos_output_paths"]:
        if "soc" in pdos_dir and skip_soc:
            print_info(f"Skipping SOC PDOS generation: `{os.path.basename(pdos_dir)}`\n")
            continue
        elif "soc" not in pdos_dir and skip_normal:
            print_info(f"Skipping non-SOC PDOS generation: `{os.path.basename(pdos_dir)}`\n")
            continue

        os.chdir(os.path.dirname(pdos_dir))
        for atomic_projection in atomic_projection_list:

            current_file += 1
            console.rule(f"Generating file {current_file} of {total_files}")

            atom, orbital = atomic_projection.split('-')

            # Checking if the PDOS file already exists
            pdos_data_file = os.path.join(os.path.dirname(pdos_dir), f"pdos_{atom}_{orbital}.dat")
            if os.path.exists(pdos_data_file):
                print_warning(f"File already exists: `{os.path.basename(pdos_data_file)}`\n")
                success_list.append(True)
                continue

            try:
                with console.status("Calculating PDOS..."):
                    # Running the sumpdos.x script to generate the PDOS files
                    run_sum_pdos((atom, orbital))

                print_success(f"Created: `{os.path.basename(pdos_data_file)}`\n")
                success_list.append(True)

            except CalledProcessError as e:
                # Handling errors
                print_error(f"Failed to generate: `{os.path.basename(pdos_data_file)}`")
                print_error(e.stderr.decode("utf-8"))
                success_list.append(False)

    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    return success_list
