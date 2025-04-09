import os
import re
from subprocess import CalledProcessError, run
from sys import argv
import matplotlib.pyplot as plt
import numpy as np
from math import sqrt

# from matplotlib.collections import LineCollection


# Usage: the following python script should be run with command line arguments in the following way:
#
# python plotting_pbands.py <compound name>
#
# For more information visit the GitHub repository (https://github.com/shayanmoosavi/Quantum-Instant-Coffee.git)


# INITIALIZATION
# ============================================================================================================================

print("Initializing...\n")

compound_name = argv[1]  # Taking the name of the compound of interest
fermi_energy = 0.0
number_of_bands = 0  # Declaring the variable
root_dir = os.path.abspath("../")  # The root directory of the project
project_dir = os.path.join(root_dir, argv[1])  # The calculation directory

include_stress_input = input(
    'Do you want to plot strain analysis instead? Type "yes" to plot strain analysis and "no" to plot normal projected bands. '
)

# Initializing the list in order to avoid having it empty and preventing from proper iteration
stress_dir_list = ["1", "1_soc"]

if include_stress_input == "yes":
    include_stress = True
else:
    include_stress = False

# The flag that comes after the file name. Namely, "_soc" for spin-orbit case and nothing otherwise
if include_stress:

    # Directory of scf calculation
    scf_dir_list = [
        os.path.join(project_dir, "scf"),
    ]

    # Directory of projected bands calculation
    pbands_dir_list = [
        os.path.join(project_dir, "projected_bands"),
    ]

    stress_amount_list_input = input("""Enter the strain amounts in units of relaxed coordinates in the form 1_<percent-of-stretch>.
For example 1_30 means the coordinates are stretched by 30%. Provide a space seperated list of DFT calculations with the specified strees amounts
like "1_<percent-of-stretch-1> 1_<percent-of-stretch-2> 1_<percent-of-stretch-2> ... ":
""")

    stress_amount_list = stress_amount_list_input.split(" ")

    stress_dir_list.clear()
    for stress_amount in stress_amount_list:
        stress_dir_list.append(os.path.join(project_dir, f"strain/{stress_amount}"))

    spin_orbit_flag = ["" for i in range(len(stress_amount_list) + 1)]
    # Skipping the spin-orbit case when plotting strain analysis
    skip_soc = True

else:
    spin_orbit_flag = ["", "_soc"]
    skip_soc = False

    # Directory of scf calculation
    scf_dir_list = [
        os.path.join(project_dir, "scf"),
        os.path.join(project_dir, "spin_orbit/scf"),
    ]

    # Directory of projected bands calculation
    pbands_dir_list = [
        os.path.join(project_dir, "projected_bands"),
        os.path.join(project_dir, "spin_orbit/projected_bands"),
    ]

# Output file directories
pw_bands_output_dir_list = []
kpdos_output_dir_list = []
scf_output_dir_list = []
projbands_dir_list = []
bands_dir_list = []

for scf_dir, pband_dir, flag in zip(
    scf_dir_list, pbands_dir_list, spin_orbit_flag
):

    pw_bands_output_dir_list.append(
        os.path.join(
            project_dir, os.path.join(pband_dir, f"{compound_name}_bands{flag}.pw.out")
        )
    )  # The output of Quantum ESPRESSO pw bands calculation

    kpdos_output_dir_list.append(
        os.path.join(
            project_dir, os.path.join(pband_dir, f"{compound_name}{flag}.kpdos.out")
        )
    )  # The output of Quantum ESPRESSO kpdos calculation

    projbands_dir_list.append(
        os.path.join(
            project_dir, os.path.join(pband_dir, f"{compound_name}{flag}.projbands")
        )
    )  # The output of Quantum ESPRESSO nscf calculation

    bands_dir_list.append(
        os.path.join(project_dir, os.path.join(pband_dir, f"{compound_name}.bands.gnu"))
    )  # The output of Quantum ESPRESSO bands calculation

    scf_output_dir_list.append(
        os.path.join(
            project_dir, os.path.join(scf_dir, f"{compound_name}_scf{flag}.pw.out")
        )
    )  # The output of Quantum ESPRESSO scf calculation

if include_stress:
    for stress_dir in stress_dir_list:

        pw_bands_output_dir_list.append(
            os.path.join(
                project_dir,
                os.path.join(stress_dir, f"{compound_name}_bands.pw.out"),
            )
        )  # The output of Quantum ESPRESSO pw bands calculation

        kpdos_output_dir_list.append(
            os.path.join(
                project_dir, os.path.join(stress_dir, f"{compound_name}.kpdos.out")
            )
        )  # The output of Quantum ESPRESSO kpdos calculation

        projbands_dir_list.append(
            os.path.join(
                project_dir, os.path.join(stress_dir, f"{compound_name}.projbands")
            )
        )  # The output of Quantum ESPRESSO nscf calculation

        bands_dir_list.append(
            os.path.join(
                project_dir, os.path.join(stress_dir, f"{compound_name}.bands.gnu")
            )
        )  # The output of Quantum ESPRESSO bands calculation

        scf_output_dir_list.append(
            os.path.join(
                project_dir, os.path.join(stress_dir, f"{compound_name}_scf.pw.out")
            )
        )  # The output of Quantum ESPRESSO scf calculation

# Getting the number of bands from Quantum ESPRESSO calculation
# ----------------------------------------------------------------------------------------------------------------------------

#List of band numbers for spin-orbit and non spin-orbit case
number_of_bands_list = []

for bands_output_dir, flag in zip(pw_bands_output_dir_list, spin_orbit_flag):
    
    print(f"Reading {compound_name}_bands{flag}.pw.out...")
    try:
        # Reading the output of Quantum ESPRESSO pw.x bands calculation
        band_output_file = open(bands_output_dir, "r")
        bands_calculation_output = band_output_file.read()
        band_output_file.close()

        # Getting the number of calculated bands from the calculation output
        band_number_regex_pattern = r"number of Kohn-Sham states=\s+(\d+)"
        band_number_regex_object = re.compile(band_number_regex_pattern)
        band_number_matches = band_number_regex_object.finditer(
            bands_calculation_output
        )

        number_of_bands = int(
            next(band_number_matches).group(1)
        )  # Accessing the value of the iterator
        number_of_bands_list.append(number_of_bands)

        print(
            f"Band number extracted successfully. There are {number_of_bands} bands in this calculation.\n"
        )

    except FileNotFoundError:
        if flag == "_soc":
            print(
                f'File "{compound_name}_bands{flag}.pw.out" does not exist. Make sure the file name is correct or \
in the directory of the project.'
            )
            skip_soc_input = input(
                'Do you want to skip spin-orbit case? Enter "yes" if you want to skip spin-orbit or \
"no" to quit the program.'
            )
            if skip_soc_input == "no":
                exit(1)
            else:
                skip_soc = True
        else:
            print(
                f'File "{compound_name}_bands{flag}.pw.out" does not exist. Make sure the file name is correct or \
in the directory of the project.'
            )
            exit(1)

print(number_of_bands_list)

#Getting the Fermi energy from Quantum ESPRESSO calculation
#----------------------------------------------------------------------------------------------------------------------------

#List of Fermi energies for spin-orbit and non spin-orbit case
fermi_energy_list = []

for scf_output_dir, flag in zip(scf_output_dir_list, spin_orbit_flag):
    
    print("Getting Fermi energy...")
    print(f"Reading {compound_name}_scf{flag}.pw.out...")
    try:
        # Reading the output of Quantum ESPRESSO nscf calculation
        scf_output_file = open(scf_output_dir, "r")
        scf_calculation_output = scf_output_file.read()
        scf_output_file.close()

        # Getting fermi energy from the calculation output
        Fermi_energy_regex_pattern = r"the Fermi energy is\s+(-?\d\.\d+)"
        Fermi_energy_regex_object = re.compile(Fermi_energy_regex_pattern)
        Fermi_energy_matches = Fermi_energy_regex_object.finditer(
            scf_calculation_output
        )

        fermi_energy = float(
            next(Fermi_energy_matches).group(1)
        )  # Accessing the value of the iterator
        fermi_energy_list.append(fermi_energy)

        print(
            f"Fermi energy extracted successfully. Fermi energy is {fermi_energy} eV.\n"
        )

    except FileNotFoundError:
        if flag == "_soc":
            print("Spin-orbit was set to be skipped. Continuing...")
            continue
        else:                
            print(
                f'File "{compound_name}_scf{flag}.pw.out" does not exist. Make sure the file name is correct or \
in the directory of the project.'
            )
            exit(1)

# Extracting projected bands from Quantum ESPRESSO calculation
# ----------------------------------------------------------------------------------------------------------------------------

# List of the numbers of atomic states for spin-orbit and non spin-orbit case
number_of_atomic_states_list = []
kpdos_calculation_output_list = []

for kpdos_output_dir, projbands_dir, fermi_energy, flag in zip(
    kpdos_output_dir_list, projbands_dir_list, fermi_energy_list, spin_orbit_flag
):
        
    print(f"Reading {compound_name}{flag}.kpdos.out...")
    print("Getting the number of bands...")

    try:
        # Reading the output of kpdos calculation
        kpdos_output_file = open(kpdos_output_dir, "r")
        kpdos_calculation_output = kpdos_output_file.read()
        kpdos_calculation_output_list.append(kpdos_calculation_output)
        kpdos_output_file.close()

        # Extracting the atomic states from output
        atomic_state_number_regex_pattern = r"natomwfc =\s+(\d+)"
        atomic_state_number_regex_object = re.compile(atomic_state_number_regex_pattern)
        atomic_state_number_matches = atomic_state_number_regex_object.finditer(
            kpdos_calculation_output
        )

        print("Getting the number of atomic states...")

        number_of_atomic_states = int(next(atomic_state_number_matches).group(1))
        number_of_atomic_states_list.append(number_of_atomic_states)

        print(f"There are {number_of_atomic_states} atomic states.")
        print("Calculating projected bands...\n")

        # Avoiding unnecessary execution of awk script
        if not os.path.exists(projbands_dir):
            try:
                run(
                    f"awk -v firststate=1 -v laststate={number_of_atomic_states} -v ef={fermi_energy} \
                    -f ./projwfc_to_bands.awk {kpdos_output_dir} > {projbands_dir}",
                    shell=True,
                    check=True,
                    capture_output=True,
                )

                print("Initialization done.\n")

            # Catching the error message
            except CalledProcessError as e:
                print(
                    "An error occurred in projected bands calculation. See below for details:\n"
                )
                print((e.stderr).decode("utf-8"))
                exit(1)

        else:
            print(f"File {compound_name}{flag}.projbands already exists!")
            print("Initialization done.\n")

    except FileNotFoundError:
        if flag == "_soc":
            if not skip_soc:
                print(
                    f'File "{compound_name}{flag}.kpdos.out" does not exist. Make sure the file name is correct or \
in the directory of the project.'
                )
                exit(1)
        else:
            print(
                f'File "{compound_name}{flag}.kpdos.out" does not exist. Make sure the file name is correct or \
in the directory of the project.'
            )
            exit(1)

# PREPROCESSING
# ============================================================================================================================

print("Preparing the atomic projection list for plotting projected bands...")

print("""
The supported orbitals are:
s, p, d, pz, px, py, dz2, dxz, dyz, dx2y2, dxy
The projection list should be in pairs of <element name>-<orbital> separated by a single space.
Example usage would be O-s C-p Fe-d
""")

failure = True

# Preventing null input and repeating asking the user to enter correct input
while failure:
    user_input = input("Enter the desired atomic orbitals you wish to project onto: ")

    if user_input == "":
        print("User input cannot be null!")
    else:
        failure = False

        # Processing the user input and extracting atomic projection information
        atomic_projection_list = []
        atomic_projections = user_input.split(" ")

        for atomic_projection in atomic_projections:
            atomic_projection_list.append(atomic_projection.split("-"))

        # Atomic orbitals and their corresponding orbital numbers
        orbital_info = {

            "s": {

                "orbital_numbers": [
                    "l=0 m= 1", 
                    "l=0 j=0.5 m_j=-0.5", 
                    "l=0 j=0.5 m_j= 0.5"
                    ],

                "orbital_coefficients": [
                    1, 
                    1/2, 
                    1/2
                ]
            },

            "p": {

                "orbital_numbers": [
                    "l=1 m= 1",
                    "l=1 m= 2",
                    "l=1 m= 3",
                    "l=1 j=0.5 m_j=-0.5",
                    "l=1 j=0.5 m_j= 0.5",
                    "l=1 j=1.5 m_j=-1.5",
                    "l=1 j=1.5 m_j=-0.5",
                    "l=1 j=1.5 m_j= 0.5",
                    "l=1 j=1.5 m_j= 1.5",
                ],

                "orbital_coefficients": [
                    1, 
                    1, 
                    1,
                    1, 
                    1, 
                    1,
                    1, 
                    1, 
                    1
                ]
            },

            "pz": {

                "orbital_numbers": [
                    "l=1 m= 1",
                    # "l=1 j=0.5 m_j=-0.5",
                    "l=1 j=0.5 m_j= 0.5",
                    # "l=1 j=1.5 m_j=-0.5",
                    "l=1 j=1.5 m_j= 0.5"
                ], 
                "orbital_coefficients": [
                    1,
                    # 1/6, 
                    1/3, # 1/6,
                    # 1/3, 
                    2/3 # 1/3
                ]
            },

            "px": {
                
                "orbital_numbers": [
                    "l=1 m= 2",
                    "l=1 j=0.5 m_j=-0.5",
                    # "l=1 j=0.5 m_j= 0.5",
                    # "l=1 j=1.5 m_j=-1.5",
                    "l=1 j=1.5 m_j=-0.5",
                    # "l=1 j=1.5 m_j= 0.5",
                    "l=1 j=1.5 m_j= 1.5"
                ],

                "orbital_coefficients": [
                    1,
                    2/6, # 1/12, 
                    # 1/12, 
                    # 1/6,
                    1/6,
                    # 1/4,
                    3/6 # 1/4 
                ]
            },
            "py": {

                "orbital_numbers": [
                    "l=1 m= 3",
                    "l=1 j=0.5 m_j=-0.5",
                    # "l=1 j=0.5 m_j= 0.5",
                    # "l=1 j=1.5 m_j=-1.5",
                    "l=1 j=1.5 m_j=-0.5",
                    # "l=1 j=1.5 m_j= 0.5",
                    "l=1 j=1.5 m_j= 1.5"
                ],

                "orbital_coefficients": [
                    1,
                    2/6, # 1/12, 
                    # 1/12, 
                    # 1/6,
                    1/6,
                    # 1/4,
                    3/6 # 1/4 
                ]
            },

            "d": {

                "orbital_numbers": [
                    "l=2 m= 1",
                    "l=2 m= 2",
                    "l=2 m= 3",
                    "l=2 m= 4",
                    "l=2 m= 5",
                    "l=2 j=1.5 m_j=-1.5",
                    "l=2 j=1.5 m_j=-0.5",
                    "l=2 j=1.5 m_j= 0.5",
                    "l=2 j=1.5 m_j= 1.5",
                    "l=2 j=2.5 m_j=-2.5",
                    "l=2 j=2.5 m_j=-1.5",
                    "l=2 j=2.5 m_j=-0.5",
                    "l=2 j=2.5 m_j= 0.5",
                    "l=2 j=2.5 m_j= 1.5",
                    "l=2 j=2.5 m_j= 2.5"
                ],

                "orbital_coefficients": [
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1,    
                    1    
                ]
            },

            "dz2": {

                "orbital_numbers": [
                    "l=2 m= 1",
                    # "l=2 j=1.5 m_j=-0.5",
                    "l=2 j=1.5 m_j= 0.5",
                    # "l=2 j=2.5 m_j=-0.5",
                    "l=2 j=2.5 m_j= 0.5"
                ], 
                "orbital_coefficients": [
                    1,
                    2/5,
                    3/5
                ]
            },

            "dxz": {
                "orbital_numbers": [
                    "l=2 m= 2",
                    # "l=2 j=1.5 m_j=-1.5",
                    "l=2 j=1.5 m_j=-0.5",
                    # "l=2 j=1.5 m_j= 0.5",
                    "l=2 j=1.5 m_j= 1.5",
                    # "l=2 j=2.5 m_j=-1.5",
                    "l=2 j=2.5 m_j=-0.5",
                    # "l=2 j=2.5 m_j= 0.5",
                    "l=2 j=2.5 m_j= 1.5"
                ],
                "orbital_coefficients": [
                    1,
                    3/10,
                    1/10,
                    2/10,
                    4/10
                ]
            },
            "dyz": {
                "orbital_numbers": [
                    "l=2 m= 3",
                    # "l=2 j=1.5 m_j=-1.5",
                    "l=2 j=1.5 m_j=-0.5",
                    # "l=2 j=1.5 m_j= 0.5",
                    "l=2 j=1.5 m_j= 1.5",
                    # "l=2 j=2.5 m_j=-1.5",
                    "l=2 j=2.5 m_j=-0.5",
                    # "l=2 j=2.5 m_j= 0.5",
                    "l=2 j=2.5 m_j= 1.5"
                ], 
                "orbital_coefficients": [
                    1,
                    3/10,
                    1/10,
                    2/10,
                    4/10
                ]
            },
            "dx2y2": {
                "orbital_numbers": [
                    "l=2 m= 4",
                    "l=2 j=1.5 m_j=-1.5",
                    # "l=2 j=1.5 m_j= 1.5",
                    # "l=2 j=2.5 m_j=-2.5",
                    "l=2 j=2.5 m_j=-1.5",
                    # "l=2 j=2.5 m_j= 1.5",
                    "l=2 j=2.5 m_j= 2.5"
                ],
                "orbital_coefficients": [
                    1,
                    4/10,
                    1/10,
                    5/10
                ]
            },
            "dxy": {
                "orbital_numbers": [
                    "l=2 m= 5",
                    "l=2 j=1.5 m_j=-1.5",
                    # "l=2 j=1.5 m_j= 1.5",
                    # "l=2 j=2.5 m_j=-2.5",
                    "l=2 j=2.5 m_j=-1.5",
                    # "l=2 j=2.5 m_j= 1.5",
                    "l=2 j=2.5 m_j= 2.5"
                ],
                "orbital_coefficients": [
                    1,
                    4/10,
                    1/10,
                    5/10
                ]
            }
        }

        atomic_projection_info_list = []

        for kpdos_calculation_output in kpdos_calculation_output_list:
            # Atomic projections and their respective indices in the projbands file
            atomic_projection_info = dict()

            for atomic_projection in atomic_projection_list:
                projection_indices_list = []

                for orbital_numbers in orbital_info[atomic_projection[1]]["orbital_numbers"]:
                    # Getting the index of all atomic states given by user input
                    atomic_state_regex_pattern = rf"state #\s+(\d+): atom\s+\d+ \({atomic_projection[0]}\s+\), wfc\s+\d+ \({orbital_numbers}\)"
                    atomic_state_regex_object = re.compile(atomic_state_regex_pattern)
                    atomic_state_number_matches = atomic_state_regex_object.finditer(
                        kpdos_calculation_output
                    )

                    for atomic_state in atomic_state_number_matches:
                        projection_indices_list.append(int(atomic_state.group(1)))
                projection_indices_list.sort()

                # px and py orbitals have the same contribution
                if atomic_projection[1] == "px" or atomic_projection[1] == "py":
                    if f"{atomic_projection[0]}-px+py" not in atomic_projection_info.keys():

                        atomic_projection_info.update(
                        {
                            f"{atomic_projection[0]}-px+py": {
                                "indices": projection_indices_list,
                                "coefficients": orbital_info[atomic_projection[1]]["orbital_coefficients"]
                            }
                        }
                    )
                    else:
                        atomic_projection_info[f"{atomic_projection[0]}-px+py"]["indices"].extend(projection_indices_list)
                        atomic_projection_info[f"{atomic_projection[0]}-px+py"]["indices"].sort()
                        
                    #     atomic_projection_info.update(
                    #     {
                    #         f"{atomic_projection[0]}-px+py": {
                    #             "indices": projection_indices_list,
                    #             "coefficients": orbital_info[atomic_projection[1]]["orbital_coefficients"]
                    #         }
                    #     }
                    # )

                # dxz and dyz orbitals have the same contribution
                elif atomic_projection[1] == "dxz" or atomic_projection[1] == "dyz":
                    if f"{atomic_projection[0]}-dxz+dyz" not in atomic_projection_info.keys():
                        atomic_projection_info.update(
                            {
                                f"{atomic_projection[0]}-dxz+dyz": {
                                "indices": projection_indices_list,
                                "coefficients": orbital_info[atomic_projection[1]]["orbital_coefficients"]
                                }
                            }
                        )
                    else:
                        atomic_projection_info[f"{atomic_projection[0]}-dxz+dyz"]["indices"].extend(projection_indices_list)
                        atomic_projection_info[f"{atomic_projection[0]}-dxz+dyz"]["indices"].sort()

                # dx2y2 and dxy orbitals have the same contribution
                elif atomic_projection[1] == "dx2y2" or atomic_projection[1] == "dxy":
                    if f"{atomic_projection[0]}-dx2y2+dxy" not in atomic_projection_info.keys():
                        atomic_projection_info.update(
                            {
                                f"{atomic_projection[0]}-dx2y2+dxy": {
                                "indices": projection_indices_list,
                                "coefficients": orbital_info[atomic_projection[1]]["orbital_coefficients"]
                                }
                            }
                        )
                    else:
                        atomic_projection_info[f"{atomic_projection[0]}-dx2y2+dxy"]["indices"].extend(projection_indices_list)
                        atomic_projection_info[f"{atomic_projection[0]}-dx2y2+dxy"]["indices"].sort()

                # else:
                #     atomic_projection_info.update(
                #         {
                #             f"{atomic_projection[0]}-{atomic_projection[1]}": projection_indices_list
                #         }
                #     )

                else:
                    atomic_projection_info.update(
                        {
                            f"{atomic_projection[0]}-{atomic_projection[1]}": {
                                "indices": projection_indices_list,
                                "coefficients": orbital_info[atomic_projection[1]]["orbital_coefficients"]
                            }
                        }
                    )

            atomic_projection_info_list.append(atomic_projection_info)

# PLOTTING THE DATA
# ============================================================================================================================

projbands_data_list = []
k_points_proj_list = []
k_points_list = []
Energy_proj_list = []
Energy_list = []

for projbands_dir, bands_dir, number_of_bands, fermi_energy in zip(
    projbands_dir_list, bands_dir_list, number_of_bands_list, fermi_energy_list
):
    # Reading the projected bands file
    projbands_data = np.loadtxt(projbands_dir)
    projbands_data_list.append(projbands_data)

    k_points_proj = np.unique(projbands_data[:, 1])
    k_points_proj_list.append(k_points_proj)

    Energy_proj = np.reshape(projbands_data[:, 2], (-1, number_of_bands))
    Energy_proj_list.append(Energy_proj)

    bands_data = np.loadtxt(os.path.join(project_dir, bands_dir))

    k_points = np.unique(bands_data[:, 0])
    k_points_list.append(k_points)

    Energy = np.reshape(bands_data[:, 1], (-1, len(k_points))) - fermi_energy
    Energy_list.append(Energy)

# Calculating the total weights
# ----------------------------------------------------------------------------------------------------------------------------

# Calculates the weights of the specified orbitals from the projbands data
def calculate_total_weights(data, atomic_state_indices, atomic_state_coefficients, number_of_bands):
    total_orbital_weights = np.zeros(len(data[:, 0]))
    for atomic_state_index in atomic_state_indices:

        # The first 4 columns are not the weights
        for coefficient in atomic_state_coefficients:
            total_orbital_weights += coefficient * data[:, atomic_state_index + 3]

    total_orbital_weights_reshaped = np.reshape(
        total_orbital_weights, (-1, number_of_bands)
    )
    return total_orbital_weights_reshaped


atomic_projection_weights_info_list = []

for atomic_projection_info, projbands_data, number_of_bands in zip(
    atomic_projection_info_list, projbands_data_list, number_of_bands_list
):
    atomic_projection_weights_info = dict()
    Energy = np.reshape(bands_data[:, 1], (-1, len(k_points)))

    elements_list = [
        atomic_projection[0] for atomic_projection in atomic_projection_list
    ]
    unique_elements_list = [
        item for i, item in enumerate(elements_list) if item not in elements_list[:i]
    ]

    number_of_subplots = len(unique_elements_list) + 1

    for atomic_projection, projection_info in atomic_projection_info.items():
        total_orbital_weight = calculate_total_weights(
            projbands_data, projection_info["indices"], projection_info["coefficients"], 
            number_of_bands
        )

        atom, orbital = atomic_projection.split('-')

        if orbital == "px" or orbital == "py":

            if f"{atom}-px+py" not in atomic_projection_weights_info.keys():
                
                atomic_projection_weights_info.update(
                    {f"{atom}-px+py": total_orbital_weight}
                )
                
        else:
            atomic_projection_weights_info.update(
                    {f"{atomic_projection}": total_orbital_weight}
                )

    atomic_projection_weights_info_list.append(atomic_projection_weights_info)

# Initializing the plotting parameters
# ----------------------------------------------------------------------------------------------------------------------------

# Read from bands.out file
high_symmetry_k_points = [0.0000, 0.5774, 0.9107, 1.5774]

k_labels = [r"$\Gamma$", r"$M$", r"$K$", r"$\Gamma$"]


def init_plot(ax, xlabel, ylabel, title, xtick_points, xtick_labels):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)  # Edit the title
    ax.set_xticks(xtick_points, xtick_labels)
    ax.grid("on")


def plot_bands(ax, xdata, ydata, data_label="data", color="blue"):
    label = ax.scatter([], [], label=data_label, color=color)

    for band in range(len(Energy)):
        ax.plot(xdata, ydata[band, :], color=color)

    return label


def plot_projbands(
    ax,
    xdata,
    ydata,
    orbital_weights,
    number_of_bands,
    spin_orbit=True,
    data_label="data",
    color="blue",
):
    label = ax.scatter([], [], label=data_label, color=color)

    # Filtering the non-zero weights
    condition = orbital_weights != 0

    # Plotting the bands
    for band in range(number_of_bands):
        x = xdata[condition[:, band]]
        y = ydata[condition[:, band], band].T
        weights = orbital_weights[condition[:, band], band]

        # Multiplying the weights by a scaling factor to get thicker bands
        weights = 2 * weights

        # points = np.array([x, y]).T.reshape(-1, 1, 2)
        # segments = np.concatenate([points[:-1], points[1:]], axis=1)

        if spin_orbit:
            # line_collections = LineCollection(segments, linewidths=weights, color=color, alpha=0.45)
            ax.scatter(x, y, s=weights, color=color, alpha=1)
        else:
            # line_collections = LineCollection(segments, linewidths=weights, color=color)
            ax.scatter(x, y, s=weights, color=color)

        # ax.add_collection(line_collections)

    return label


orbital_plot_color_info = {
    "s": "#FF00ED",
    "p": "#0BF317",
    "d": "#FF2B11",
    "pz": "#0D3EE0",
    "px+py": "#0BF317",
    "dz2": "#0D3EE0",
    "dxz+dyz": "#0BF317",
    "dx2y2+dxy": "#FF2B11",
}

atomic_projection_plot_info_list = []

for atomic_projection_weights_info in atomic_projection_weights_info_list:
    atomic_projection_plot_info = dict()

    for i in range(len(unique_elements_list)):
        orbitals_list = []
        orbitals_plot_color_list = []
        orbital_weights_list = []
        atomic_projections_list = []

        for orbital, orbital_plot_color in orbital_plot_color_info.items():

            atomic_projection = f"{unique_elements_list[i]}-{orbital}"

            if atomic_projection in atomic_projection_weights_info.keys():
                atomic_projection_list.append(atomic_projection)
                orbitals_list.append(orbital)
                orbitals_plot_color_list.append(orbital_plot_color_info[orbital])
                orbital_weights_list.append(
                    atomic_projection_weights_info[atomic_projection]
                )

        atomic_projection_plot_info.update(
            {
                f"{unique_elements_list[i]}": {
                    "index": i + 1,
                    "projected_orbitals": orbitals_list,
                    "plot_colors": orbitals_plot_color_list,
                    "orbital_weights": orbital_weights_list,
                }
            }
        )

    atomic_projection_plot_info_list.append(atomic_projection_plot_info)

# Creating the LaTeX symbols for the comopound name to display in the plot
# ----------------------------------------------------------------------------------------------------------------------------

compound_name_regex_pattern = r"(([A-Z][a-z]?)(\d?))"
compound_name_regex_object = re.compile(compound_name_regex_pattern)
element_matches = compound_name_regex_object.finditer(compound_name)

element_names = []
element_numbers = []
for element in element_matches:
    element_names.append(element.group(2))
    if element.group(3) == "":
        element_numbers.append(1)
    else:
        element_numbers.append(int(element.group(3)))

compound_name_latex = r"$"

for i in range(len(element_names)):
    compound_name_latex += r"{" + rf"{element_names[i]}" + r"}"
    if element_numbers[i] != 1:
        compound_name_latex += r"_" + r"{" + rf"{element_numbers[i]}" + r"}"

compound_name_latex += r"$"

# Plotting the data
# ----------------------------------------------------------------------------------------------------------------------------

if include_stress:
    stress_amount_list.insert(0, "1")
else:
    stress_amount_list = ["1", "1_soc"]

for (
    atomic_projection_plot_info,
    k_points,
    Energy,
    k_points_proj,
    Energy_proj,
    number_of_bands,
    flag,
    stress_amount
) in zip(
    atomic_projection_plot_info_list,
    k_points_list,
    Energy_list,
    k_points_proj_list,
    Energy_proj_list,
    number_of_bands_list,
    spin_orbit_flag,
    stress_amount_list
):

    # plt.style.use("ggplot")

    fig, axs = plt.subplots(1, number_of_subplots, sharey=True, layout="constrained")

    fig.set_figheight(6)
    fig.set_figwidth(12)

    if flag == "_soc":
        fig.suptitle(
            "Projected Band Structure for "
            + compound_name_latex
            + "with Spin-Orbit Coupling"
        )
    else:
        if include_stress:
            if stress_amount == "1":
                fig.suptitle(
                    "Projected Band Structure for "
                    + compound_name_latex
                    + "without Spin-Orbit Coupling"
                )
            else:
                fig.suptitle(
                    "Projected Band Structure for "
                    + compound_name_latex
                    + f"with {stress_amount.replace('_', '.')}"
                    + r"$a_0$"
                )
        else:
            fig.suptitle(
                "Projected Band Structure for "
                + compound_name_latex
                + "without Spin-Orbit Coupling"
            )

    init_plot(axs[0], "k", "E (eV)", "TOTAL", high_symmetry_k_points, k_labels)
    bands_label = plot_bands(axs[0], k_points, Energy, "total", "blue")
    axs[0].legend(
        handles=[
            bands_label,
        ]
    )
    axs[0].grid("on")

    for element in atomic_projection_plot_info.keys():
        legend_labels = []

        for i in range(len(atomic_projection_plot_info[element]["projected_orbitals"])):
            init_plot(
                axs[atomic_projection_plot_info[element]["index"]],
                "k",
                "E (eV)",
                element,
                high_symmetry_k_points,
                k_labels,
            )

            if flag == "_soc":
                label = plot_projbands(
                    axs[atomic_projection_plot_info[element]["index"]],
                    k_points_proj,
                    Energy_proj,
                    atomic_projection_plot_info[element]["orbital_weights"][i],
                    number_of_bands,
                    True,
                    atomic_projection_plot_info[element]["projected_orbitals"][i],
                    atomic_projection_plot_info[element]["plot_colors"][i],
                )
            else:
                label = plot_projbands(
                    axs[atomic_projection_plot_info[element]["index"]],
                    k_points_proj,
                    Energy_proj,
                    atomic_projection_plot_info[element]["orbital_weights"][i],
                    number_of_bands,
                    False,
                    atomic_projection_plot_info[element]["projected_orbitals"][i],
                    atomic_projection_plot_info[element]["plot_colors"][i],
                )

            legend_labels.append(label)

        axs[atomic_projection_plot_info[element]["index"]].legend(loc="lower center", handles=legend_labels)

    plt.ylim(-3, 3)
    # if include_stress:
    #     plt.savefig(os.path.join(project_dir, f"{compound_name}_projbands{stress_amount}.png"))
    # else:
    #     plt.savefig(os.path.join(project_dir, f"{compound_name}_projbands{flag}_testing.png"))
    plt.show()
