"""Module for managing file paths."""

import os
from sys import argv
from config import load_config
from input_handler import get_pbands_type, get_strain_amounts


def validate_command_line_args(args):
    """
    Validate command line arguments.

    Args:
    args (list): List of command line arguments.

    Returns:
        str: The compound name provided as a command line argument.

    Raises:
        SystemExit: If the compound name argument is missing.
    """
    if len(args) < 2:
        print("Error: Missing compound name argument")
        print("Usage: python <script>.py <compound_name>")
        exit(1)
    return args[1]


def get_project_directory(compound_name):
    """
    Get the project directory for the given compound.

    Args:
        compound_name (str): Name of the compound.

    Returns:
        str: The absolute path to the project directory.
    """
    root_dir = os.path.abspath("../")  # The root directory of the project
    return os.path.join(root_dir, compound_name)  # The calculation directory


def add_paths_for_directories(
    scf_dir_list,
    pbands_dir_list,
    spin_orbit_flag,
    compound_name,
    file_patterns,
    pw_bands_output_paths,
    kpdos_output_paths,
    scf_output_paths,
    projbands_paths,
    bands_paths,
):
    """
    Add file paths for SCF and projected bands directories.

    Args:
        scf_dir_list (list): List of SCF directories.
        pbands_dir_list (list): List of projected bands directories.
        spin_orbit_flag (list): List of spin-orbit flags.
        compound_name (str): Name of the compound.
        file_patterns (dict): Dictionary of file name patterns.
        pw_bands_output_paths (list): List to store PW bands output paths.
        kpdos_output_paths (list): List to store KPDOS output paths.
        scf_output_paths (list): List to store SCF output paths.
        projbands_paths (list): List to store projbands paths.
        bands_paths (list): List to store bands output paths.
    """
    for scf_dir, pband_dir, flag in zip(scf_dir_list, pbands_dir_list, spin_orbit_flag):

        # The output of Quantum ESPRESSO PW Bands calculation
        pw_bands_output_paths.append(
            os.path.join(
                pband_dir,
                file_patterns["bands_output"].format(
                    compound_name=compound_name, flag=flag
                ),
            )
        )

        # The output of Quantum ESPRESSO KPDOS calculation
        kpdos_output_paths.append(
            os.path.join(
                pband_dir,
                file_patterns["kpdos_output"].format(
                    compound_name=compound_name, flag=flag
                ),
            )
        )

        # The output of projbands file from projwfc_to_bands.awk script
        projbands_paths.append(
            os.path.join(
                pband_dir,
                file_patterns["projbands_output"].format(
                    compound_name=compound_name, flag=flag
                ),
            )
        )

        # The output of Quantum ESPRESSO Bands calculation
        bands_paths.append(
            os.path.join(
                pband_dir,
                file_patterns["bands_gnu"].format(compound_name=compound_name),
            )
        )

        # The output of Quantum ESPRESSO SCF calculation
        scf_output_paths.append(
            os.path.join(
                scf_dir,
                file_patterns["scf_output"].format(
                    compound_name=compound_name, flag=flag
                ),
            )
        )


def add_strain_paths(
    stress_dir,
    compound_name,
    file_patterns,
    pw_bands_output_paths,
    kpdos_output_paths,
    scf_output_paths,
    projbands_paths,
    bands_paths,
):
    """
    Add file paths for strain analysis.

    Args:
        stress_dir (str): Directory for strain analysis.
        compound_name (str): Name of the compound.
        file_patterns (dict): Dictionary of file name patterns.
        pw_bands_output_paths (list): List to store PW bands output paths.
        kpdos_output_paths (list): List to store KPDOS output paths.
        scf_output_paths (list): List to store SCF output paths.
        projbands_paths (list): List to store projbands paths.
        bands_paths (list): List to store bands output paths.
    """
    # The output of Quantum ESPRESSO PW Bands calculation
    pw_bands_output_paths.append(
        os.path.join(
            stress_dir,
            file_patterns["bands_output"].format(compound_name=compound_name, flag=""),
        )
    )

    # The output of Quantum ESPRESSO KPDOS calculation
    kpdos_output_paths.append(
        os.path.join(
            stress_dir,
            file_patterns["kpdos_output"].format(compound_name=compound_name, flag=""),
        )
    )

    # The output of projbands file from projwfc_to_bands.awk script
    projbands_paths.append(
        os.path.join(
            stress_dir,
            file_patterns["projbands_output"].format(
                compound_name=compound_name, flag=""
            ),
        )
    )

    # The output of Quantum ESPRESSO Bands calculation
    bands_paths.append(
        os.path.join(
            stress_dir, file_patterns["bands_gnu"].format(compound_name=compound_name)
        )
    )

    # The output of Quantum ESPRESSO SCF calculation
    scf_output_paths.append(
        os.path.join(
            stress_dir,
            file_patterns["scf_output"].format(compound_name=compound_name, flag=""),
        )
    )


def build_file_paths(
    project_dir, compound_name, include_stress, config, stress_amounts=None
):
    """
    Build file paths based on the analysis type.

    Args:
        project_dir (str): Path to the project directory.
        compound_name (str): Name of the compound.
        include_stress (bool): Whether to include stress analysis.
        config (dict): Configuration dictionary.
        stress_amounts (list, optional): List of strain amounts. Defaults to None.

    Returns:
        dict: Dictionary containing lists of file paths and a skip SOC flag.
    """
    # Initializing paths lists
    pw_bands_output_paths = []
    kpdos_output_paths = []
    scf_output_paths = []
    projbands_paths = []
    bands_paths = []

    # Getting directory structure from config
    dir_structure = config["directory_structure"]
    file_patterns = config["file_patterns"]

    if include_stress:
        # For strain analysis
        scf_dir_list = [os.path.join(project_dir, dir_structure["scf"])]
        pbands_dir_list = [os.path.join(project_dir, dir_structure["projected_bands"])]

        # The flag that comes after the file name. Namely, "_soc" for spin-orbit case and nothing otherwise
        spin_orbit_flag = [""]
        skip_soc = True

        # Add paths for normal calculation
        add_paths_for_directories(
            scf_dir_list,
            pbands_dir_list,
            spin_orbit_flag,
            compound_name,
            file_patterns,
            pw_bands_output_paths,
            kpdos_output_paths,
            scf_output_paths,
            projbands_paths,
            bands_paths,
        )

        # Add paths for each strain amount
        stress_dir_list = [
            os.path.join(project_dir, f"{dir_structure['strain']}/{amount}")
            for amount in stress_amounts
        ]

        for stress_dir in stress_dir_list:
            add_strain_paths(
                stress_dir,
                compound_name,
                file_patterns,
                pw_bands_output_paths,
                kpdos_output_paths,
                scf_output_paths,
                projbands_paths,
                bands_paths,
            )

    else:
        # For normal projected bands
        spin_orbit_flag = ["", "_soc"]
        skip_soc = False

        scf_dir_list = [
            os.path.join(project_dir, dir_structure["scf"]),
            os.path.join(project_dir, dir_structure["scf_soc"]),
        ]

        pbands_dir_list = [
            os.path.join(project_dir, dir_structure["projected_bands"]),
            os.path.join(project_dir, dir_structure["projected_bands_soc"]),
        ]

        add_paths_for_directories(
            scf_dir_list,
            pbands_dir_list,
            spin_orbit_flag,
            compound_name,
            file_patterns,
            pw_bands_output_paths,
            kpdos_output_paths,
            scf_output_paths,
            projbands_paths,
            bands_paths,
        )

    return {
        "pw_bands_output_paths": pw_bands_output_paths,
        "kpdos_output_paths": kpdos_output_paths,
        "scf_output_paths": scf_output_paths,
        "projbands_paths": projbands_paths,
        "bands_paths": bands_paths,
        "skip_soc": skip_soc,
    }


def prepare_paths():
    """
    Prepare paths for the Quantum ESPRESSO calculations.

    Returns:
        dict: Dictionary containing compound name, project directory, stress inclusion flag, paths, and stress amounts.
    """
    print("Initializing...\n")

    config = load_config()

    compound_name = validate_command_line_args(argv)

    project_dir = get_project_directory(compound_name)

    include_stress = get_pbands_type()

    stress_amounts = get_strain_amounts() if include_stress else None

    paths = build_file_paths(
        project_dir, compound_name, include_stress, config, stress_amounts
    )

    return {
        "compound_name": compound_name,
        "project_dir": project_dir,
        "include_stress": include_stress,
        "paths": paths,
        "stress_amounts": stress_amounts,
    }


# Test to ensure the module works as expected
if __name__ == "__main__":
    calculation = prepare_paths()

    # Checking if all required files exist
    failure = False
    for paths in list(calculation["paths"].values())[:-1]:
        for path in paths:
            if not os.path.exists(path):
                print(f"path '{path}' does not exist!")
                failure = True
            else:
                print(f"path '{path}' exists.")

    if failure:
        print("Test failed!")
        exit(1)
    else:
        print("Test passed!")

    print("Test information for debugging: \n")

    print(f"Compound Name: {calculation['compound_name']}")
    print(f"Project Directory: {calculation['project_dir']}")
    print(f"Include Stress: {calculation['include_stress']}")
    print(f"Stress Amounts: {calculation['stress_amounts']}")
    print("\nDirectory Structure:")
    for key, value in calculation["paths"].items():
        print(f"{key}: {value}")
