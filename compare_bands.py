import os
from sys import argv
import numpy as np
import matplotlib.pyplot as plt
import re


# Usage: the following python script should be run with command line arguments in the following way:
#
# python compare_bands.py <compound name>
#
# For more information visit the GitHub repository (https://github.com/shayanmoosavi/Quantum-Instant-Coffee.git)


# INITIALIZATION
# ===========================================================================================================================================

print("Initializing...\n", flush=True)

compound_name = argv[1]  # Taking the name of the compound of interest
root_dir = os.path.abspath("../")  # The root directory of the project
project_dir = os.path.join(root_dir, argv[1])  # The calculation directory

# Directory of projected bands calculation
pbands_dir_list = [
    os.path.join(project_dir, "projected_bands"), os.path.join(project_dir, "spin_orbit/projected_bands")
]

# Directory of wannier calculation
wannier_dir_list = [
    os.path.join(project_dir, "wannier"), os.path.join(project_dir, "spin_orbit/wannier")
]
# The flag that comes after the file name. Namely, "_soc" for spin-orbit case and nothing otherwise
spin_orbit_flag = ["", "_soc"]

# Output file directories
bands_dir_list = []
wannier_bands_dir_list = []
wannier_nscf_output_dir_list = []

for wannier_dir, pband_dir, flag in zip(wannier_dir_list, pbands_dir_list, spin_orbit_flag):

    wannier_nscf_output_dir_list.append(os.path.join(project_dir,
    os.path.join(wannier_dir, f"{compound_name}_nscf_wannier{flag}.pw.out")))  # The output of Quantum ESPRESSO nscf wannier calculation

# Getting the Fermi energy from Quantum ESPRESSO calculation
# -------------------------------------------------------------------------------------------------------------------------------------------

fermi_energy_list = [] # List of Fermi energies for spin-orbit and non spin-orbit case
alat_parameter_list = [] # List of alat parmaeters for spin-orbit and non spin-orbit case
skip_normal = False  # Flag to dermine whether non spin-orbit coupling case should be skipped
for wannier_nscf_output_dir, flag in zip(wannier_nscf_output_dir_list, spin_orbit_flag):

    print("Getting alat parameter...\n", flush=True)
    print(f"Reading {compound_name}_nscf_wannier{flag}.pw.out...\n", flush=True)
    try:

        # Reading the output of Quantum ESPRESSO nscf calculation
        nscf_output_file = open(wannier_nscf_output_dir, "r")
        nscf_calculation_output = nscf_output_file.read()
        nscf_output_file.close()

        # Getting fermi energy from the calculation output
        alat_parameter_regex_pattern = r"celldm\(1\)=\s+(\d\.\d+)"
        alat_parameter_regex_object = re.compile(alat_parameter_regex_pattern)
        alat_parameter_match = alat_parameter_regex_object.finditer(nscf_calculation_output)

        if alat_parameter_match is not None:
            alat_parameter = float(next(alat_parameter_match).group(1)) * 0.529177  # Converting bohr to angstrom
            alat_parameter_list.append(alat_parameter)
        else:
            print("FATAL ERROR: Alat parameter not found!")
            exit(1)

        print(f"Alat parameter extracted successfully. Alat parameter is {alat_parameter} Angstrom.\n")

        print("Getting Fermi energy...\n", flush=True)

        # Getting the number of calculated bands from the calculation output
        Fermi_energy_regex_pattern = r"the Fermi energy is\s+(-?\d\.\d+)"
        Fermi_energy_regex_object = re.compile(Fermi_energy_regex_pattern)
        Fermi_energy_match = Fermi_energy_regex_object.finditer(nscf_calculation_output)

        if Fermi_energy_match is not None:
            fermi_energy = float(next(Fermi_energy_match).group(1))  # Accessing the value of the iterator
            fermi_energy_list.append(fermi_energy)
            print(f"Fermi energy extracted successfully. Fermi energy is {fermi_energy} eV.\n", flush=True)
        else:
            print("FATAL ERROR: Fermi energy not found!")
            exit(1)
        
        bands_dir_list.append(os.path.join(project_dir,
        os.path.join(pband_dir, f"{compound_name}.bands.gnu")))  # The plot output of Quantum ESPRESSO bands calculation

        wannier_bands_dir_list.append(os.path.join(project_dir,
        os.path.join(wannier_dir, f"{compound_name}_wannier{flag}_band.dat")))  # The plot output of wannier calculation

    except FileNotFoundError:
        if flag == "":
            print(f"File \"{compound_name}_nscf_wannier{flag}.pw.out\" does not exist. Make sure the file name is correct or \
in the directory of the project.")
            skip_normal_input = input('''Do you want to plot non spin-orbit case as well? Enter \"no\" if you want to
continue without non spin-orbit case or \"yes\" to quit the program: ''')
            if skip_normal_input == "no":
                skip_normal = True
            else:
                exit(1)
        else:
            print(f"File \"{compound_name}_nscf_wannier{flag}.pw.out\" does not exist. Make sure the file name is correct or \
in the directory of the project.")
            exit(1)

# PREPROCESSING
# ===========================================================================================================================================

wannier_data_list = []  # List of wannier bands data
DFT_data_list = []  # List of DFT bands data
k_points_wannier_list = []  # List of kpoints for wannier calculation
k_points_DFT_list = []  # List of kpoints for DFT calculation
wannier_energies_list = []  # The energies column of wannier bands data
DFT_energies_list = []  # The energies column of DFT bands data

# Extracting the bands data from
for wannier_bands_dir, bands_dir, alat_parameter, fermi_energy in zip(wannier_bands_dir_list, bands_dir_list, 
alat_parameter_list, fermi_energy_list):
    
    wannier_data = np.loadtxt(wannier_bands_dir)
    DFT_data = np.loadtxt(bands_dir)

    k_points_wannier = np.unique(wannier_data[:, 0]) / ((2 * np.pi) / alat_parameter)
    wannier_energies = np.reshape(wannier_data[:, 1], (-1, len(k_points_wannier))) - fermi_energy

    k_points_DFT = np.unique(DFT_data[:, 0])
    DFT_energies = np.reshape(DFT_data[:, 1], (-1, len(k_points_DFT))) - fermi_energy
        
    wannier_data_list.append(wannier_data)
    DFT_data_list.append(DFT_data)
    k_points_wannier_list.append(k_points_wannier)
    k_points_DFT_list.append(k_points_DFT)
    wannier_energies_list.append(wannier_energies)
    DFT_energies_list.append(DFT_energies)

# PLOTTING THE DATA
# ===========================================================================================================================================

high_symmetry_k_points = [0.0000, 0.5774, 0.9107, 1.5774]

k_labels = [r"$\Gamma$", r"$M$", r"$K$", r"$\Gamma$"]

# Creating the LaTeX symbols for the comopound name to display in the plot
# ----------------------------------------------------------------------------------------------------------------------------

compound_name_regex_pattern = r"(([A-Z][a-z]?)(\d?))"
compound_name_regex_object = re.compile(compound_name_regex_pattern)
element_matches = compound_name_regex_object.finditer(compound_name)

element_names = []
element_numbers = []
for element in element_matches:
    element_names.append(element.group(2))
    if element.group(3) == '':
        element_numbers.append(1)
    else:
        element_numbers.append(int(element.group(3)))

compound_name_latex = r'$'

for i in range(len(element_names)):
    compound_name_latex +=  r'{' + rf"{element_names[i]}" + r'}'
    if element_numbers[i] != 1:
        compound_name_latex += r'_' + r'{' + rf"{element_numbers[i]}" + r'}'

compound_name_latex += r'$'

for k_points_DFT, DFT_energies, k_points_wannier, wannier_energies, flag in zip(k_points_DFT_list, DFT_energies_list, 
k_points_wannier_list, wannier_energies_list, spin_orbit_flag):

    plt.style.use("ggplot")
    plt.xlabel("k")
    plt.ylabel("E (eV)")

    if skip_normal:
        plt.title("Projected Band Structure for " + compound_name_latex + "with Spin-Orbit Coupling")
    else:
        if flag == '':
            plt.title("Projected Band Structure for " + compound_name_latex + "without Spin-Orbit Coupling")
        else:
            plt.title("Projected Band Structure for " + compound_name_latex + "with Spin-Orbit Coupling")
    
    plt.xticks(high_symmetry_k_points, k_labels)

    plt.plot([], [], color="red", label="Wannier")
    for band in range(len(wannier_energies)):
        plt.plot(k_points_wannier, wannier_energies[band, :], color="red")

    plt.plot([], [], color="blue", label="DFT")
    for band in range(len(DFT_energies)):
        plt.plot(k_points_DFT, DFT_energies[band, :], color="blue")

    plt.ylim(-5, 2)
    plt.legend(loc=(0.4, 0.6))
    plt.savefig(os.path.join(project_dir, f"{compound_name}_wannier_compare_bands{flag}.png"))       
    plt.show()
