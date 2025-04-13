"""Functions for managing file paths."""

import os


def validate_command_line_args(argv):
    """Validate command line arguments."""
    if len(argv) < 2:
        print("Error: Missing compound name argument")
        print("Usage: python plot_pbands.py <compound_name>")
        exit(1)
    return argv[1]


def get_project_directory(compound_name):
    """Get the project directory."""
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
    """Add paths for the given directories."""
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
    """Add paths for strain analysis."""

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
    """Build file paths based on the analysis type."""

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
