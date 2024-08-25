import os
from sys import argv
import re
import subprocess

# Usage: the following python script should be run with command line arguments in the following way
#
# python init_calc.py <compound name> <path-to-POSCAR-file>
#
# For more information visit the GitHub repository (https://github.com/shayanmoosavi/Quantum-Instant-Coffee.git)

# INITIALIZATION
# =======================================================================================================

print("Initializing...\n", flush=True)

compound_name = argv[1]  # Taking the name of the compound of interest
poscar_file = argv[2]  # The POSCAR file for the atomic structure

print("Recognizing elements...", flush=True)

# Parsing the compound name for elements and their numbers
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

number_of_atoms = sum(element_numbers)  # The number of atoms in the compound
atom_types = len(element_names)  # The number of atom types in the compound

print(f"Total number of atoms found: {number_of_atoms}", flush=True)
print(f"Number of distinct atom types found: {atom_types}", flush=True)

atomic_labels = []
for element_name, element_number in zip(element_names, element_numbers):
    for _ in range(element_number):
        atomic_labels.append(element_name)

print("Recognized elements: ", end='', flush=True)

for element_name in element_names:
    print(element_name, end=' ')

root_dir = os.path.abspath("../")  # The root directory for creating the calculation project
project_dir = os.path.join(root_dir, argv[1])
calculation_list = ("scf", "pdos", "projected_bands", "wannier")  # List of desired DFT and wannier calculations
calculation_dirs = []  # Directories of calculations

# Creating the folder structure of the project
try:
    os.mkdir(project_dir)
    print(f"\nProject directory initialized at:\n {project_dir}\n", flush=True)

    print(f"Entering {compound_name} directory...")
    os.chdir(project_dir)

    for calculation in calculation_list:
        os.mkdir(calculation)
        calculation_dirs.append(os.path.abspath(calculation))

    os.mkdir("spin_orbit")
    for calculation in calculation_list:
        calculation_with_soc = os.path.join("spin_orbit", calculation)
        os.makedirs(calculation_with_soc)
        calculation_dirs.append(os.path.abspath(calculation_with_soc))

    print("Successfully created calculation directories.\n", flush=True)

except FileExistsError:
    print("Project already initialized! Retrieving calculation directories...\n")
    for dirpath, dirnames, _ in os.walk(project_dir):
        if len(dirnames) == 0:
            calculation_dirs.append(dirpath)

# TEMPLATE INPUT FILE GENERATION
# =======================================================================================================

print("Generating template input files...\n", flush=True)
print(
'''
By default, the number of bands in spin-orbit case will be double of the provided number of bands below.
Change the generated input files if that's not what you want.
''', flush=True)
number_of_bands = int(input("Enter the number of bands: "))

# Reading the atomic positions and lattice vectors from the POSCAR file
with open(poscar_file, "r") as file:
    poscar_file_content = file.read()

    # The pattern for 3 decimal numbers with 16 significant digits
    coordinates_regex_pattern = r"(-?\d\d?\.\d{16})\s+(-?\d\d?\.\d{16})\s+(-?\d\d?\.\d{16})"
    coordinates_regex_object = re.compile(coordinates_regex_pattern)
    coordinates_matches = coordinates_regex_object.finditer(poscar_file_content)
    lattice_vectors = []
    atomic_positions = []

    counter = 0
    for match in coordinates_matches:

        # The first 3 matches are lattice vectors and the rest are atomic positions
        if counter > 2:
            atomic_positions.append(f"{match.group(1)}  {match.group(2)}    {match.group(3)}")
        else:
            lattice_vectors.append(f"{match.group(1)}  {match.group(2)}    {match.group(3)}")
        counter += 1

# Input file contents
#-----------------------------------------------------------------------------------------------------

# Input file for Quantum ESPRESSO vc-relax calculation
vc_relax_input = \
f'''
 &CONTROL
  calculation      = 'vc-relax' 
  outdir           = './out' 
  pseudo_dir       = '../../Pseudopotentials' 
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
  tprnfor          = .true.
  tstress          = .true.
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 50 
  ecutrho          = 500
 /
 &ELECTRONS
  conv_thr         = 1e-12
  electron_maxstep = 600
 /
 &IONS
 /
 &CELL
  cell_dofree      = 'fixc'
 /
ATOMIC_SPECIES  ! Enter atom information here
'''

# Input file for Quantum ESPRESSO vc-relax calculation with spin-orbit coupling
vc_relax_soc_input = \
f'''
 &CONTROL
  calculation      = 'vc-relax' 
  outdir           = './out' 
  pseudo_dir       = '../../../Pseudopotentials_rel' 
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
  tprnfor          = .true.
  tstress          = .true.
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 60 
  ecutrho          = 600
  occupations      = 'smearing'
  smearing         = 'fermi-dirac'
  degauss          = 0.005
  lforcet          = .true.
  lspinorb         = .true.
  noncolin         = .true.
 /
 &ELECTRONS
  conv_thr         = 1e-12
  electron_maxstep = 600
  mixing_beta      = 0.4
  startingpot      = 'file'
 /
 &IONS
 /
 &CELL
  cell_dofree      = 'fixc'
 /
ATOMIC_SPECIES  ! Enter atom information here 
'''

for element in element_names:
    vc_relax_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"
    vc_relax_soc_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"

vc_relax_input += \
'''
ATOMIC_POSITIONS crystal
'''

vc_relax_soc_input += \
'''
ATOMIC_POSITIONS crystal
'''

# Dynamically adding the atomic positions and lattice vectors to the input files
for atomic_position, atomic_label in zip(atomic_positions, atomic_labels):
    vc_relax_input += f"\t{atomic_label}\t{atomic_position}\n"
    vc_relax_soc_input += f"\t{atomic_label}\t{atomic_position}\n"

vc_relax_input += '''K_POINTS automatic 
  12 12 1   0 0 0 
CELL_PARAMETERS angstrom
'''
vc_relax_soc_input += '''K_POINTS automatic 
  10 10 1   0 0 0 
CELL_PARAMETERS angstrom
'''

for lattice_vector in lattice_vectors:
    vc_relax_input += f"\t{lattice_vector}\n"
    vc_relax_soc_input += f"\t{lattice_vector}\n"

# Input file for Quantum ESPRESSO scf calculation
scf_input = \
f'''
 &CONTROL
  calculation      = 'scf' 
  outdir           = './out' 
  pseudo_dir       = '../../Pseudopotentials' 
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
  tprnfor          = .true.
  tstress          = .true.
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 50 
  ecutrho          = 500
  occupations      = 'smearing'
  smearing         = 'fermi-dirac'
  degauss          = 0.005
 /
 &ELECTRONS
  conv_thr         = 1e-12
  electron_maxstep = 600
 /
ATOMIC_SPECIES  ! Enter atom information here
'''

# Input file for Quantum ESPRESSO scf calculation with spin-orbit coupling
scf_soc_input = \
f'''
 &CONTROL
  calculation      = 'scf' 
  outdir           = './out' 
  pseudo_dir       = '../../../Pseudopotentials_rel' 
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
  tprnfor          = .true.
  tstress          = .true.
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 60 
  ecutrho          = 600
  occupations      = 'smearing'
  smearing         = 'fermi-dirac'
  degauss          = 0.005
  lforcet          = .true.
  lspinorb         = .true.
  noncolin         = .true.
 /
 &ELECTRONS
  conv_thr         = 1e-11
  electron_maxstep = 600
  mixing_beta      = 0.4
  startingpot      = 'file'
 /
ATOMIC_SPECIES  ! Enter atom information here
'''

for element in element_names:
    scf_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"
    scf_soc_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"

scf_input += \
'''
ATOMIC_POSITIONS crystal
'''

scf_soc_input += \
'''
ATOMIC_POSITIONS crystal
'''

# Dynamically adding the atomic positions and lattice vectors to the input files
for atomic_position, atomic_label in zip(atomic_positions, atomic_labels):
    scf_input += f"\t{atomic_label}\t{atomic_position}\n"
    scf_soc_input += f"\t{atomic_label}\t{atomic_position}\n"

scf_input += '''K_POINTS automatic
  14 14 1   0 0 0 
CELL_PARAMETERS angstrom
'''

scf_soc_input = '''K_POINTS automatic 
  14 14 1   0 0 0
CELL_PARAMETERS angstrom
'''

for lattice_vector in lattice_vectors:
    scf_input += f"\t{lattice_vector}\n"
    scf_soc_input += f"\t{lattice_vector}\n"

# Input file for Quantum ESPRESSO nscf calculation
nscf_input = \
f'''
 &CONTROL
  calculation      = 'nscf' 
  outdir           = './out' 
  pseudo_dir       = '../../Pseudopotentials' 
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
  tprnfor          = .true.
  tstress          = .true.
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 50 
  ecutrho          = 500
  nbnd             = {number_of_bands}
  occupations      = 'smearing'
  smearing         = 'fermi-dirac'
  degauss          = 0.005
 /
 &ELECTRONS
  conv_thr         = 1e-12
  electron_maxstep = 600
 /
ATOMIC_SPECIES  ! Enter atom information here
'''

# Input file for Quantum ESPRESSO nscf calculation with spin-orbit coupling
nscf_soc_input = \
f'''
 &CONTROL
  calculation      = 'nscf' 
  outdir           = './out' 
  pseudo_dir       = '../../../Pseudopotentials_rel'
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
  tprnfor          = .true.
  tstress          = .true.
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 50 
  ecutrho          = 500
  nbnd             = {2 * number_of_bands}
  occupations      = 'smearing'
  smearing         = 'fermi-dirac'
  degauss          = 0.005
  lforcet          = .true.
  lspinorb         = .true.
  noncolin         = .true.
 /
 &ELECTRONS
  conv_thr         = 1e-12
  electron_maxstep = 600
 /
ATOMIC_SPECIES  ! Enter atom information here
'''

for element in element_names:
    nscf_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"
    nscf_soc_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"

nscf_input += \
'''
ATOMIC_POSITIONS crystal
'''

nscf_soc_input += \
'''
ATOMIC_POSITIONS crystal
'''

# Dynamically adding the atomic positions and lattice vectors to the input files
for atomic_position, atomic_label in zip(atomic_positions, atomic_labels):
    nscf_input += f"\t{atomic_label}\t{atomic_position}\n"
    nscf_soc_input += f"\t{atomic_label}\t{atomic_position}\n"

nscf_input += '''K_POINTS automatic 
  28 28 1   0 0 0 
CELL_PARAMETERS angstrom
'''

nscf_soc_input += '''K_POINTS automatic 
  18 18 1   0 0 0
CELL_PARAMETERS angstrom
'''

for lattice_vector in lattice_vectors:
    nscf_input += f"\t{lattice_vector}\n"
    nscf_soc_input += f"\t{lattice_vector}\n"

# Input file for Quantum ESPRESSO pdos calculation
pdos_input = \
f'''
 &PROJWFC
   outdir          = './out'
   prefix          = '{compound_name}' 
   filpdos         = '{compound_name}' 
   DeltaE          = 0.01 
 /

'''

pdos_soc_input = pdos_input

# Input file for Quantum ESPRESSO bands calculation
pw_bands_input = \
f'''
 &CONTROL
  calculation      = 'bands' 
  outdir           = './out' 
  pseudo_dir       = '../../Pseudopotentials' 
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 50 
  ecutrho          = 500
  nbnd             = {number_of_bands}
  occupations      = 'smearing'
  smearing         = 'fermi-dirac'
  degauss          = 0.005
 /
 &ELECTRONS
  conv_thr         = 1e-12
  electron_maxstep = 600
 /
ATOMIC_SPECIES  ! Enter atom information here
'''

# Input file for Quantum ESPRESSO bands calculation with spin-orbit coupling
pw_bands_soc_input = \
f'''
 &CONTROL
  calculation      = 'bands' 
  outdir           = './out' 
  pseudo_dir       = '../../../Pseudopotentials_rel' 
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 50 
  ecutrho          = 500
  nbnd             = {2 * number_of_bands}
  occupations      = 'smearing'
  smearing         = 'fermi-dirac'
  degauss          = 0.005
  lforcet          = .true.
  lspinorb         = .true.
  noncolin         = .true.
 /
 &ELECTRONS
  conv_thr         = 1e-12
  electron_maxstep = 600
 /
ATOMIC_SPECIES  ! Enter atom information here
'''

for element in element_names:
    pw_bands_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"
    pw_bands_soc_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"

pw_bands_input += \
'''
ATOMIC_POSITIONS crystal
'''

pw_bands_soc_input += \
'''
ATOMIC_POSITIONS crystal
'''

# Dynamically adding the atomic positions and lattice vectors to the input files
for atomic_position, atomic_label in zip(atomic_positions, atomic_labels):
    pw_bands_input += f"\t{atomic_label}\t{atomic_position}\n"
    pw_bands_soc_input += f"\t{atomic_label}\t{atomic_position}\n"

pw_bands_input += '''K_POINTS crystal_b 
4
  0.0000000000    0.0000000000    0.0000000000    120 ! Gamma
  0.5000000000    0.0000000000    0.0000000000    120 ! M
  0.3333333333    0.3333333333    0.0000000000    120 ! K
  0.0000000000    0.0000000000    0.0000000000    0 ! Gamma 
CELL_PARAMETERS angstrom
'''

pw_bands_soc_input += '''K_POINTS crystal_b 
4
  0.0000000000    0.0000000000    0.0000000000    120 ! Gamma
  0.5000000000    0.0000000000    0.0000000000    120 ! M
  0.3333333333    0.3333333333    0.0000000000    120 ! K
  0.0000000000    0.0000000000    0.0000000000    0 ! Gamma 
CELL_PARAMETERS angstrom
'''

for lattice_vector in lattice_vectors:
    pw_bands_input += f"\t{lattice_vector}\n"
    pw_bands_soc_input += f"\t{lattice_vector}\n"

# Input file for Quantum ESPRESSO bands extraction and symmetry calculations
bands_input = \
f'''
 &BANDS
  prefix  = '{compound_name}'
  outdir  = './out'
  lsym    = .true.
  filband = '{compound_name}.bands' 
 /

'''

bands_soc_input = bands_input

# Input file for Quantum ESPRESSO kpdos calculation
kpdos_input = \
f'''
 &PROJWFC
  outdir       = './out'
  prefix       = '{compound_name}'
  ngauss       = -99 ! Fermi-Dirac
  degauss      = 0.005
  DeltaE       = 0.01
  kresolveddos = .true.
  filpdos      = '{compound_name}.k'
  lsym         = .false.
  filproj      = '{compound_name}.proj.dat'
 /

'''

kpdos_soc_input = kpdos_input

# Input file for Quantum ESPRESSO nscf calculation for usage in wannier function calculation
nscf_wannier_input = \
f'''
 &CONTROL
  calculation      = 'nscf' 
  outdir           = './out' 
  pseudo_dir       = '../../Pseudopotentials'
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
  tprnfor          = .true.
  tstress          = .true.
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 50 
  ecutrho          = 500
  nbnd             = {number_of_bands}
  occupations      = 'smearing'
  smearing         = 'fermi-dirac'
  degauss          = 0.005
 /
 &ELECTRONS
  conv_thr         = 1e-12
  electron_maxstep = 600
 /
ATOMIC_SPECIES  ! Enter atom information here
'''

# Input file for Quantum ESPRESSO nscf calculation with spin-orbit coupling 
# for usage in wannier function calculation
nscf_wannier_soc_input = \
f'''
 &CONTROL
  calculation      = 'nscf' 
  outdir           = './out' 
  pseudo_dir       = '../../../Pseudopotentials_rel'
  prefix           = '{compound_name}' 
  verbosity        = 'high' 
  etot_conv_thr    = 1e-9 
  forc_conv_thr    = 1e-7
  tprnfor          = .true.
  tstress          = .true.
 /
 &SYSTEM
  ibrav            = 0 
  nat              = {number_of_atoms}
  ntyp             = {atom_types}
  ecutwfc          = 50 
  ecutrho          = 500
  nbnd             = {2 * number_of_bands}
  occupations      = 'smearing'
  smearing         = 'fermi-dirac'
  degauss          = 0.005
  lforcet          = .true.
  lspinorb         = .true.
  noncolin         = .true.
  nosym            = .true.
 /
 &ELECTRONS
  conv_thr         = 1e-12
  electron_maxstep = 600
 /
ATOMIC_SPECIES  ! Enter atom information here
'''

for element in element_names:
    nscf_wannier_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"
    nscf_wannier_soc_input += f"\t{element}\t{element}_weight\t{element}_Pseudo_pot\n"

nscf_wannier_input += \
'''
ATOMIC_POSITIONS crystal
'''

nscf_wannier_soc_input += \
'''
ATOMIC_POSITIONS crystal
'''

# Dynamically adding the atomic positions and lattice vectors to the input files
for atomic_position, atomic_label in zip(atomic_positions, atomic_labels):
    nscf_wannier_input += f"\t{atomic_label}\t{atomic_position}\n"
    nscf_wannier_soc_input += f"\t{atomic_label}\t{atomic_position}\n"

nscf_wannier_input += "CELL_PARAMETERS angstrom\n"
nscf_wannier_soc_input += "CELL_PARAMETERS angstrom\n"

for lattice_vector in lattice_vectors:
    nscf_wannier_input += f"\t{lattice_vector}\n"
    nscf_wannier_soc_input += f"\t{lattice_vector}\n"

# Running the kmesh.pl utility script provided by Quantum ESPRESSO in order to get the kpoint mesh of desired density
kpoints = subprocess.run(f"../kmesh.pl 28 28 1", shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
kpoints_soc = subprocess.run(f"../kmesh.pl 18 18 1", shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")

# Adding the created kpoint mesh to the input files
nscf_wannier_input += kpoints
nscf_wannier_soc_input += kpoints_soc

# Input file for Wannier90
wannier_input = \
f'''
num_bands = {number_of_bands} ! number of bands
num_wann  = 0 ! Enter the number of wannier projections here
num_iter  = 200 ! number of minimization iterations

! disentaglement
! Enter the appropriate energy windows here
dis_win_min  = 0 ! lower bound of bands to extract
dis_win_max  = 0 ! upper bound of bands to extract
!dis_froz_min = 0 ! lower bound of inner window
!dis_froz_max = 0 ! upper bound of innesr window
dis_num_iter = 3000 ! number of disentanglement iterations

! Writing the tight-binding Hamiltonian
write_hr = true

! plotting the interpolated band structure
bands_plot = true
begin kpoint_path
G 0.0000000000  0.0000000000  0.0000000000  M 0.5000000000  0.0000000000  0.0000000000
M 0.5000000000  0.0000000000  0.0000000000  K 0.3333333333  0.3333333333  0.0000000000
K 0.3333333333  0.3333333333  0.0000000000  G 0.0000000000  0.0000000000  0.0000000000
end kpoint_path

begin projections  ! Enter the atomic projections here
'''

# Input file for Wannier90 with spin-orbit coupling
wannier_soc_input = \
f'''
num_bands = {2 * number_of_bands} ! number of bands
num_wann  = 0 ! Enter the number of wannier projections here
num_iter  = 200 ! number of minimization iterations

! disentaglement
! Enter the appropriate energy windows here
dis_win_min  = 0 ! lower bound of bands to extract
dis_win_max  = 0 ! upper bound of bands to extract
!dis_froz_min = 0 ! lower bound of inner window
!dis_froz_max = 0 ! upper bound of innesr window
dis_num_iter = 3000 ! number of disentanglement iterations

! Writing the tight-binding Hamiltonian
write_hr = true

! plotting the interpolated band structure
bands_plot = true
begin kpoint_path
G 0.0000000000  0.0000000000  0.0000000000  M 0.5000000000  0.0000000000  0.0000000000
M 0.5000000000  0.0000000000  0.0000000000  K 0.3333333333  0.3333333333  0.0000000000
K 0.3333333333  0.3333333333  0.0000000000  G 0.0000000000  0.0000000000  0.0000000000
end kpoint_path

begin projections  ! Enter the atomic projections here
'''

for element in element_names:
    wannier_input += f"{element}: proj\n"
    wannier_soc_input += f"{element}: proj\n"

wannier_input += \
'''end projections

begin unit_cell_cart
angstrom
'''

wannier_soc_input += \
'''end projections

! Required for spin orbit
spinors = true

begin unit_cell_cart
angstrom
'''

# Dynamically adding the atomic positions and lattice vectors to the input files
for lattice_vector in lattice_vectors:
    wannier_input += f"\t{lattice_vector}\n"
    wannier_soc_input += f"\t{lattice_vector}\n"

wannier_input += '''end unit_cell_cart

begin atoms_frac
'''

wannier_soc_input += '''end unit_cell_cart

begin atoms_frac
'''

for atomic_position, atomic_label in zip(atomic_positions, atomic_labels):
    wannier_input += f"\t{atomic_label}\t{atomic_position}\n"
    wannier_soc_input += f"\t{atomic_label}\t{atomic_position}\n"

wannier_input += '''end atoms_frac

mp_grid = 28 28 1

begin kpoints
'''

wannier_soc_input += '''end atoms_frac

mp_grid = 18 18 1

begin kpoints
'''

# Running the kmesh.pl utility script provided by Quantum ESPRESSO in order to get the kpoint mesh of desired density
kpoints_wannier = subprocess.run(f"../kmesh.pl 28 28 1 wann", shell=True, 
stdout=subprocess.PIPE).stdout.decode("utf-8")
kpoints_soc_wannier = subprocess.run(f"../kmesh.pl 18 18 1 wann", shell=True, 
stdout=subprocess.PIPE).stdout.decode("utf-8")

# Adding the created kpoint mesh to the input files
wannier_input += kpoints_wannier
wannier_input += "end kpoints\n"
wannier_soc_input += kpoints_soc_wannier
wannier_soc_input += "end kpoints\n"

# Input file for Quantum ESPRESSO pw2wan calculation 
pw2wan_input = \
f'''
&inputpp
  outdir     =  './out'   ! quantum espresso outdir
  prefix     =  '{compound_name}' ! prefix of the pw.x scf calculation
  seedname   =  '{compound_name}_wannier' ! must be same as the file name of win file
  write_amn  =  .true.
  write_mmn  =  .true.
  write_unk  =  .true.
  reduce_unk =  .true.
/

'''

pw2wan_soc_input = \
f'''
&inputpp
  outdir     =  './out'   ! quantum espresso outdir
  prefix     =  '{compound_name}' ! prefix of the pw.x scf calculation
  seedname   =  '{compound_name}_wannier_soc' ! must be same as the file name of win file
  write_amn  =  .true.
  write_mmn  =  .true.
  write_unk  =  .true.
  reduce_unk =  .true.
/

'''

# Calculation types and their respective input files nicely formatted for convenience and easy access
calculation_info = {
    "scf": {
        "index": 0,
        "input_list": (vc_relax_input, scf_input), 
        "filename_list": (f"{compound_name}_vc_relax.pw.in", f"{compound_name}_scf.pw.in")
    },
    "pdos": {
        "index": 1,
        "input_list": (nscf_input, pdos_input), 
        "filename_list": (f"{compound_name}_nscf.pw.in", f"{compound_name}.pdos.in")
    },
    "projected_bands": {
        "index": 2,
        "input_list": (pw_bands_input, bands_input, kpdos_input), 
        "filename_list": (f"{compound_name}_bands.pw.in", f"{compound_name}.bands.in", f"{compound_name}.kpdos.in")
    },
    "wannier": {
        "index": 3,
        "input_list": (nscf_wannier_input, wannier_input, pw2wan_input), 
        "filename_list": (f"{compound_name}_nscf_wannier.pw.in", f"{compound_name}_wannier.win", f"{compound_name}.pw2wan.in")
    }
}

calculation_soc_info = {
    "scf": {
        "index": 4,
        "input_list": (vc_relax_soc_input, scf_soc_input), 
        "filename_list": (f"{compound_name}_vc_relax_soc.pw.in", f"{compound_name}_scf_soc.pw.in")
    },
    "pdos": {
        "index": 5,
        "input_list": (nscf_soc_input, pdos_soc_input), 
        "filename_list": (f"{compound_name}_nscf_soc.pw.in", f"{compound_name}_soc.pdos.in")
    },
    "projected_bands": {
        "index": 6,
        "input_list": (pw_bands_soc_input, bands_soc_input, kpdos_soc_input), 
        "filename_list": (f"{compound_name}_bands_soc.pw.in", f"{compound_name}_soc.bands.in", f"{compound_name}_soc.kpdos.in")
    },
    "wannier": {
        "index": 7,
        "input_list": (nscf_wannier_soc_input, wannier_soc_input, pw2wan_soc_input), 
        "filename_list": (f"{compound_name}_nscf_wannier_soc.pw.in", f"{compound_name}_wannier_soc.win", f"{compound_name}_soc.pw2wan.in")
    }
}

# Writing the generated templates to files
for calculation in calculation_list:
    for input_src, filename in zip(calculation_info[calculation]["input_list"], calculation_info[calculation]["filename_list"]):

        with open(os.path.join(calculation_dirs[calculation_info[calculation]["index"]], filename), "w") as file:
            file.write(input_src)
        print(f"Wrote {filename} at:\n \
{os.path.join(calculation_dirs[calculation_info[calculation]["index"]], filename)}\n", flush=True)
    
    for input_src, filename in zip(calculation_soc_info[calculation]["input_list"], calculation_soc_info[calculation]["filename_list"]):

        with open(os.path.join(calculation_dirs[calculation_soc_info[calculation]["index"]], filename), "w") as file:
            file.write(input_src)
        print(f"Wrote {filename} at:\n \
{os.path.join(calculation_dirs[calculation_soc_info[calculation]["index"]], filename)}\n", flush=True)

print("\nInput files have been gererated successfully.")