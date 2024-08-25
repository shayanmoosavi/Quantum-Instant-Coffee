import os
from sys import argv
import numpy as np
import matplotlib.pyplot as plt
import re
from subprocess import run, CalledProcessError
from math import sqrt
from matplotlib.collections import LineCollection


# Usage: the following python script should be run with command line arguments in the following way
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

# Path of awk script provided by Quantum ESPRESSO to calculate projected bands
projwfc_to_bands_dir = os.path.join(root_dir, "projwfc_to_bands.awk")

# Directory of projected bands calculation
pbands_dir_list = [
    os.path.join(project_dir, "projected_bands"), os.path.join(project_dir, "spin_orbit/projected_bands")
]  

# Directory of pdos calculation
pdos_dir_list = [
    os.path.join(project_dir, "pdos"), os.path.join(project_dir, "spin_orbit/pdos")
]

# The flag that comes after the file name. Namely, "_soc" for spin-orbit case and nothing otherwise
spin_orbit_flag = ["", "_soc"]  

# Output file directories
pw_bands_output_dir_list = []
kpdos_output_dir_list = []
nscf_output_dir_list = []
projbands_dir_list = []
bands_dir_list = []

for pband_dir, flag in zip(pbands_dir_list, spin_orbit_flag):

    pw_bands_output_dir_list.append(os.path.join(project_dir, 
    os.path.join(pband_dir, f"{compound_name}_bands{flag}.pw.out")))  # The output of Quantum ESPRESSO pw bands calculation

    kpdos_output_dir_list.append(os.path.join(project_dir, 
    os.path.join(pband_dir, f"{compound_name}{flag}.kpdos.out")))  # The output of Quantum ESPRESSO kpdos calculation

    projbands_dir_list.append(os.path.join(project_dir, 
        os.path.join(pband_dir, f"{compound_name}{flag}.projbands")))  # The output of Quantum ESPRESSO nscf calculation

    bands_dir_list.append(os.path.join(project_dir, 
    os.path.join(pband_dir, f"{compound_name}.bands.gnu")))  # The output of Quantum ESPRESSO bands calculation

    # kpdos_output_dir = os.path.join(project_dir, f"{compound_name}.kpdos.out")  # The output of Quantum ESPRESSO kpdos calculation
    # nscf_output_dir = os.path.join(project_dir, f"{compound_name}_nscf.pw.out")  # The output of Quantum ESPRESSO nscf calculation
    # projbands_dir = os.path.join(project_dir, f"{compound_name}.projbands")  # The output directory of the awk script

for pdos_dir, flag in zip(pdos_dir_list, spin_orbit_flag):

    nscf_output_dir_list.append(os.path.join(project_dir, 
        os.path.join(pdos_dir, f"{compound_name}_nscf{flag}.pw.out")))  # The output of Quantum ESPRESSO nscf calculation

# Getting the number of bands from Quantum ESPRESSO calculation
# ----------------------------------------------------------------------------------------------------------------------------

# List of band numbers for spin-orbit and non spin-orbit case
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
        band_number_matches = band_number_regex_object.finditer(bands_calculation_output)
        
        number_of_bands = int(next(band_number_matches).group(1))  # Accessing the value of the iterator
        number_of_bands_list.append(number_of_bands)
        
        print(f"Band number extracted successfully. There are {number_of_bands} bands in this calculation.\n")

    except FileNotFoundError:
        print(f"File \"{compound_name}_bands{flag}.pw.out\" does not exist. Make sure the file name is correct or \
in the directory of the project.")
        exit(1)

# Getting the Fermi energy from Quantum ESPRESSO calculation
# ----------------------------------------------------------------------------------------------------------------------------

# List of Fermi energies for spin-orbit and non spin-orbit case
fermi_energy_list = []

for nscf_output_dir, flag in zip(nscf_output_dir_list, spin_orbit_flag):

    print(f"Reading {compound_name}_nscf{flag}.pw.out...")
    print("Getting Fermi energy...")
    try:

        # Reading the output of Quantum ESPRESSO pw.x bands calculation
        nscf_output_file = open(nscf_output_dir, "r")
        nscf_calculation_output = nscf_output_file.read()
        nscf_output_file.close()

        # Getting the number of calculated bands from the calculation output
        Fermi_energy_regex_pattern = r"the Fermi energy is\s+(-?\d\.\d+)"
        Fermi_energy_regex_object = re.compile(Fermi_energy_regex_pattern)
        Fermi_energy_matches = Fermi_energy_regex_object.finditer(nscf_calculation_output)
        
        fermi_energy = float(next(Fermi_energy_matches).group(1))  # Accessing the value of the iterator
        fermi_energy_list.append(fermi_energy)
        
        print(f"Fermi energy extracted successfully. Fermi energy is {fermi_energy} eV.\n")

    except FileNotFoundError:
        print(f"File \"{compound_name}_nscf{flag}.pw.out\" does not exist. Make sure the file name is correct or \
in the directory of the project.")
        exit(1)

# Extracting projected bands from Quantum ESPRESSO calculation
# ----------------------------------------------------------------------------------------------------------------------------

# List of the numbers of atomic states for spin-orbit and non spin-orbit case
number_of_atomic_states_list = []
kpdos_calculation_output_list = []

for kpdos_output_dir, projbands_dir, fermi_energy, flag in zip(kpdos_output_dir_list, projbands_dir_list, 
fermi_energy_list, spin_orbit_flag):

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
        atomic_state_number_matches = atomic_state_number_regex_object.finditer(kpdos_calculation_output)

        print("Getting the number of atomic states...")

        number_of_atomic_states = int(next(atomic_state_number_matches).group(1))
        number_of_atomic_states_list.append(number_of_atomic_states)

        print(f"There are {number_of_atomic_states} atomic states.")
        print(f"Calculating projected bands...\n")

        # Avoiding unnecessary execution of awk script
        if not os.path.exists(projbands_dir):

            try:
                run(f"awk -v firststate=1 -v laststate={number_of_atomic_states} -v ef={fermi_energy} \
                    -f {projwfc_to_bands_dir} {kpdos_output_dir} > {projbands_dir}", shell=True, check=True, 
                    capture_output=True)

                print("Initialization done.\n")
            
            # Catching the error message
            except CalledProcessError as e:
                print("An error occurred in projected bands calculation. See below for details:\n")
                print((e.stderr).decode("utf-8"))
                exit(1)

        else:
            print(f"File {compound_name}{flag}.projbands already exists!")
            print("Initialization done.\n")

    except FileNotFoundError:
        print(f"File \"{compound_name}{flag}.kpdos.out\" does not exist. Make sure the file name is correct or \
in the directory of the project.")
        exit(1)

# PREPROCESSING
# ============================================================================================================================

print("Preparing the atomic projection list for plotting projected bands...")

print('''
The supported orbitals are:
s, p, d, pz, px, py, dz2, dxz, dyz, dx2y2, dxy
The projection list should be in pairs of <element name>-<orbital> separated by a single space.
Example usage would be O-s C-p Fe-d
''')

failure = True

# Preventing null input and repeating asking the user to enter correct input
while failure:
    user_input = input("Enter the desired atomic orbitals you wish to project onto: ")

    if user_input == '':
        print("User input cannot be null!")
    else:
        failure = False

        # Processing the user input and extracting atomic projection information
        atomic_projection_list = []
        atomic_projections = user_input.split(' ')

        for atomic_projection in atomic_projections:
            atomic_projection_list.append(atomic_projection.split('-'))
        
        # Atomic orbitals and their corresponding orbital numbers
        orbital_info = {
            "s": [
                "l=0 m= 1", 
                "l=0 j=0.5 m_j=-0.5", "l=0 j=0.5 m_j= 0.5"
            ],

            "p": [
                "l=1 m= 1", "l=1 m= 2", "l=1 m= 3", 
                "l=1 j=0.5 m_j=-0.5", "l=1 j=0.5 m_j= 0.5", "l=1 j=1.5 m_j=-1.5", 
                "l=1 j=1.5 m_j=-0.5", "l=1 j=1.5 m_j= 0.5", "l=1 j=1.5 m_j= 1.5"
            ],

            "pz": [
                "l=1 m= 1",
                "l=1 j=0.5 m_j=-0.5", "l=1 j=0.5 m_j= 0.5", 
                "l=1 j=1.5 m_j=-0.5", "l=1 j=1.5 m_j= 0.5"
            ],
            "px": [
                "l=1 m= 2",
                "l=1 j=0.5 m_j=-0.5", "l=1 j=0.5 m_j= 0.5", "l=1 j=1.5 m_j=-1.5", 
                "l=1 j=1.5 m_j=-0.5", "l=1 j=1.5 m_j= 0.5", "l=1 j=1.5 m_j= 1.5"
            ],
            "py": [
                "l=1 m= 3",
                "l=1 j=0.5 m_j=-0.5", "l=1 j=0.5 m_j= 0.5", "l=1 j=1.5 m_j=-1.5", 
                "l=1 j=1.5 m_j=-0.5", "l=1 j=1.5 m_j= 0.5", "l=1 j=1.5 m_j= 1.5"
            ],

            "d": [
                "l=2 m= 1", "l=2 m= 2", "l=2 m= 3", "l=2 m= 4", "l=2 m= 5",
                "l=2 j=1.5 m_j=-1.5", "l=2 j=1.5 m_j=-0.5", "l=2 j=1.5 m_j= 0.5", "l=2 j=1.5 m_j= 1.5", "l=2 j=2.5 m_j=-2.5",
                "l=2 j=2.5 m_j=-1.5", "l=2 j=2.5 m_j=-0.5", "l=2 j=2.5 m_j= 0.5", "l=2 j=2.5 m_j= 1.5", "l=2 j=2.5 m_j= 2.5"
            ],

            "dz2": [
                "l=2 m= 1",
                "l=2 j=2.5 m_j=-0.5", "l=2 j=2.5 m_j= 0.5",
                "l=2 j=1.5 m_j=-0.5", "l=2 j=1.5 m_j= 0.5"
            ],

            "dxz": [
                "l=2 m= 2",
                "l=2 j=2.5 m_j=-1.5", "l=2 j=2.5 m_j=-0.5", "l=2 j=2.5 m_j= 0.5", "l=2 j=2.5 m_j= 1.5",
                "l=2 j=1.5 m_j=-1.5", "l=2 j=1.5 m_j=-0.5", "l=2 j=1.5 m_j= 0.5", "l=2 j=1.5 m_j= 1.5"
            ],

            "dyz": [
                "l=2 m= 3",
                "l=2 j=2.5 m_j=-1.5", "l=2 j=2.5 m_j=-0.5", "l=2 j=2.5 m_j= 0.5", "l=2 j=2.5 m_j= 1.5",
                "l=2 j=1.5 m_j=-1.5", "l=2 j=1.5 m_j=-0.5", "l=2 j=1.5 m_j= 0.5", "l=2 j=1.5 m_j= 1.5"
            ],

            "dx2y2": [
                "l=2 m= 4",
                "l=2 j=2.5 m_j=-2.5", "l=2 j=2.5 m_j=-1.5", "l=2 j=1.5 m_j=-1.5",
                "l=2 j=2.5 m_j= 2.5", "l=2 j=2.5 m_j= 1.5", "l=2 j=1.5 m_j= 1.5"
            ],

            "dxy": [
                "l=2 m= 5",
                "l=2 j=2.5 m_j=-2.5", "l=2 j=2.5 m_j=-1.5", "l=2 j=1.5 m_j=-1.5",
                "l=2 j=2.5 m_j= 2.5", "l=2 j=2.5 m_j= 1.5", "l=2 j=1.5 m_j= 1.5"
            ]
        }

        atomic_projection_indices_info_list = []

        for kpdos_calculation_output in kpdos_calculation_output_list:

            # Atomic projections and their respective indices in the projbands file
            atomic_projection_indices_info = dict()

            for atomic_projection in atomic_projection_list:
                projection_indices_list = []

                for orbital in orbital_info[atomic_projection[1]]:

                    # Getting the index of all atomic states given by user input
                    atomic_state_regex_pattern = rf"state #\s+(\d+): atom\s+\d+ \({atomic_projection[0]}\s+\), wfc\s+\d+ \({orbital}\)"
                    atomic_state_regex_object = re.compile(atomic_state_regex_pattern)
                    atomic_state_number_matches = atomic_state_regex_object.finditer(kpdos_calculation_output)

                    for atomic_state in atomic_state_number_matches:
                        projection_indices_list.append(int(atomic_state.group(1)))
                projection_indices_list.sort()
                
                # px and py orbitals have the same contribution
                if atomic_projection[1] == "px" or atomic_projection[1] == "py":
                    if "px+py" not in atomic_projection_indices_info.keys():
                        atomic_projection_indices_info.update({f"{atomic_projection[0]}-px+py": projection_indices_list})

                # dxz and dyz orbitals have the same contribution
                elif atomic_projection[1] == "dxz" or atomic_projection[1] == "dyz":
                    if "dxz+dyz" not in atomic_projection_indices_info.keys():
                        atomic_projection_indices_info.update({f"{atomic_projection[0]}-dxz+dyz": projection_indices_list})

                # dx2y2 and dxy orbitals have the same contribution
                elif atomic_projection[1] == "dx2y2" or atomic_projection[1] == "dxy":
                    if "dx2y2+dxy" not in atomic_projection_indices_info.keys():
                        atomic_projection_indices_info.update({f"{atomic_projection[0]}-dx2y2+dxy": projection_indices_list})

                else:
                    atomic_projection_indices_info.update({f"{atomic_projection[0]}-{atomic_projection[1]}": 
                    projection_indices_list})

            atomic_projection_indices_info_list.append(atomic_projection_indices_info)

# PLOTTING THE DATA
# ============================================================================================================================

projbands_data_list = []
k_points_proj_list = []
k_points_list = []
Energy_proj_list = []
Energy_list = []

for projbands_dir, bands_dir, number_of_bands, fermi_energy \
    in zip(projbands_dir_list, bands_dir_list, number_of_bands_list, fermi_energy_list):

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

#Calculates the weights of the specified orbitals from the projbands data
def calculate_total_weights(data, atomic_state_indices, number_of_bands):
    total_orbital_weights = np.zeros(len(data[:, 0]))
    for atomic_state_index in atomic_state_indices:
        # The first 4 columns are not the weights
        total_orbital_weights += data[:, atomic_state_index + 3]

    total_orbital_weights_reshaped = np.reshape(total_orbital_weights, (-1, number_of_bands))
    return total_orbital_weights_reshaped

atomic_projection_weights_info_list = []

for atomic_projection_indices_info, projbands_data, number_of_bands \
    in zip(atomic_projection_indices_info_list, projbands_data_list, number_of_bands_list):

    atomic_projection_weights_info = dict()
    Energy = np.reshape(bands_data[:, 1], (-1, len(k_points)))

    elements_list = [atomic_projection[0] for atomic_projection in atomic_projection_list]
    unique_elements_list = [item for i, item in enumerate(elements_list) if item not in elements_list[:i]]

    number_of_subplots = len(unique_elements_list) + 1

    for atomic_projection, indices in atomic_projection_indices_info.items():
        total_orbital_weight = calculate_total_weights(projbands_data, indices, number_of_bands)
        atomic_projection_weights_info.update({f"{atomic_projection}": total_orbital_weight})

    atomic_projection_weights_info_list.append(atomic_projection_weights_info)

# Initializing the plotting parameters
# ----------------------------------------------------------------------------------------------------------------------------

# Read from bands.out file
high_symmetry_k_points = [0.0000, 0.5774, 0.9107, 1.5774]

k_labels = [r"$\Gamma$", r"$M$", r"$K$", r"$\Gamma$"]

def init_plot(ax, xlabel, ylabel, title, xtick_points,
    xtick_labels):

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)  # Edit the title
    ax.set_xticks(xtick_points, xtick_labels)

def plot_bands(ax, xdata, ydata, data_label="data", color="blue"):

    label = ax.scatter([], [], label=data_label, color=color)

    for band in range(len(Energy)):
        ax.plot(xdata, ydata[band, :], color=color)
    
    return label

def plot_projbands(ax, xdata, ydata, orbital_weights, number_of_bands, spin_orbit = True, data_label="data", color="blue"):

    label = ax.scatter([], [], label=data_label, color=color)

    # Filtering the non-zero weights
    condition = orbital_weights != 0

    # Plotting the bands
    for band in range(number_of_bands):
        
        x = xdata[condition[:, band]]
        y = ydata[condition[:, band], band].T
        weights = orbital_weights[condition[:, band], band]
        weights = 3 * weights[:-1]  # Multiplying the weights by a scaling factor to get thicker bands
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        if spin_orbit:
            line_collections = LineCollection(segments, linewidths=weights, color=color, alpha=0.45)
        else:
            line_collections = LineCollection(segments, linewidths=weights, color=color)
        
        ax.add_collection(line_collections)

    return label

orbital_plot_color_info = {
    "s": "magenta",
    "p": "green",
    "d": "red",
    "pz": "blue",
    "px+py": "green",
    "dz2": "blue",
    "dxz+dyz": "green",
    "dx2y2+dxy": "red"
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
            if atomic_projection in atomic_projection_indices_info.keys():
                atomic_projection_list.append(atomic_projection)
                orbitals_list.append(orbital)
                orbitals_plot_color_list.append(orbital_plot_color_info[orbital])
                orbital_weights_list.append(atomic_projection_weights_info[atomic_projection])
                
        atomic_projection_plot_info.update({f"{unique_elements_list[i]}":{"index": i + 1, "projected_orbitals": orbitals_list,
        "plot_colors": orbitals_plot_color_list, "orbital_weights": orbital_weights_list}})
    
    atomic_projection_plot_info_list.append(atomic_projection_plot_info)

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

for atomic_projection_plot_info, flag, k_points, Energy, k_points_proj, Energy_proj, number_of_bands, spin_orbit_state \
    in zip(atomic_projection_plot_info_list, spin_orbit_flag, k_points_list, Energy_list, 
    k_points_proj_list, Energy_proj_list, number_of_bands_list, [False, True]):

    plt.style.use("ggplot")

    fig, axs = plt.subplots(1, number_of_subplots, sharey=True, layout="constrained")

    fig.set_figheight(6)
    fig.set_figwidth(12)

    if spin_orbit_state:
        fig.suptitle("Projected Band Structure for " + compound_name_latex + "Without Spin-Orbit Coupling")
    else:
        fig.suptitle("Projected Band Structure for " + compound_name_latex + "With Spin-Orbit Coupling")

    init_plot(axs[0], "k", "E (eV)", "TOTAL", high_symmetry_k_points, k_labels)
    bands_label = plot_bands(axs[0], k_points, Energy, "total", "blue")
    axs[0].legend(handles=[bands_label, ])

    for element in atomic_projection_plot_info.keys():

        legend_labels = []

        for i in range(len(atomic_projection_plot_info[element]["projected_orbitals"])):
            
            init_plot(axs[atomic_projection_plot_info[element]["index"]], "k", "E (eV)", 
            element, high_symmetry_k_points, k_labels)
            
            label = plot_projbands(axs[atomic_projection_plot_info[element]["index"]], k_points_proj, Energy_proj, 
            atomic_projection_plot_info[element]["orbital_weights"][i], number_of_bands, spin_orbit_state,
            atomic_projection_plot_info[element]["projected_orbitals"][i], 
            atomic_projection_plot_info[element]["plot_colors"][i])

            legend_labels.append(label)

        axs[atomic_projection_plot_info[element]["index"]].legend(
            handles=legend_labels)


    plt.ylim(-3, 3)
    plt.savefig(os.path.join(project_dir, f"{compound_name}_projbands{flag}.png"))
    plt.show()
