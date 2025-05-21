# Quantum Instant Coffee ![Static Badge](https://img.shields.io/badge/Input%20file%20generator-red) ![Static Badge](https://img.shields.io/badge/Easy%20plotting-red) ![Static Badge](https://img.shields.io/badge/Preprocessing-red) ![Static Badge](https://img.shields.io/badge/Postprocessing-red)
> An instant input file generator and plotting scripts for Quantum ESPRESSO and Wannier90

<div align="center">
<img src="Logo.png" align="center"/>
</div>

## 📚 Table of Contents
- [About](#-about)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Features](#-features)
- [Troubleshooting](#-troubleshooting)
- [Usage](#-usage)
- [Limitations](#-limitations)
- [Configuration](#-configuration)
- [License](#-license)
- [Contributing](#-contributing)
- [Acknowledgements](#-acknowledgements)

## 💡 About
Quantum Instant Coffee streamlines quantum materials calculations by automatically generating input files for [Quantum ESPRESSO](https://www.quantum-espresso.org) and [Wannier90](https://wannier.org/). It supports essential calculations including:

- **Self-Consistent Field** (scf)
- **Projected Density of States** (pdos)
- **Projected Band Structure** (projected_bands)
- **Wannier interpolated bands** (wannier)

The input files will be generated both with and without considering spin-orbit coupling, with files organized a clear directory structure.

### 🧰 Toolkit:
- `input_file_writer.py`: Generates input files for common QE/Wannier90 workflows
- `projected_bands_plotter.py`: Plots projected band structures
- `pdos_plotter.py`: Plots projected density of states
- `compare_bands.py`: Compares DFT bands with Wannier-interpolated bands 

## 📦 Requirements
- Tested on Python 3.10
- Numpy
- Matplotlib
- Pandas
- Rich
- PyYAML
- BeautifulSoup4 (Optional, for fetching the atomic weights table from IUPAC website)
- Requests (Optional, for fetching the atomic weights table from IUPAC website)
- lxml (Optional, for fetching the atomic weights table from IUPAC website)
- [Quantum ESPRESSO](https://www.quantum-espresso.org) (for running the calculations)
- [Wannier90](https://wannier.org/) (for running the calculations)

## 🔧 Installation

### 1 - Get the repository
Clone the repository:

```bash
git clone https://github.com/shayanmoosavi/Quantum-Instant-Coffee.git 
````

Or download the latest release from the releases section of the repository.

### 2 - Install the required packages
To install the required packages, you can use pip.

For all the dependencies:
```bash
pip install numpy matplotlib pandas rich beautifulsoup4 requests lxml
```

For the required packages:
```bash
pip install numpy matplotlib pandas rich
```

### 3 - Install the repository as a package
To install the repository as a package, navigate to the cloned directory and run:

```bash
pip install .
```

## ✨ Features

### Input File Generation
- Automatically generates all necessary input files for QE and Wannier90
- Supports both standard and spin-orbit coupling calculations
- Organizes files in a logical directory structure

### Visualization Tools
- Projected band structure plotting with customizable projection options
- PDOS visualization with element-specific contributions
- Comparative analysis of DFT vs Wannier interpolated bands

## 🔍 Troubleshooting

### Missing Pseudopotentials
If you encounter errors about missing pseudopotentials, ensure you have:
1. Downloaded the appropriate pseudopotential files
2. Updated the paths in the generated input files

## 📖 Usage
In order to use these scripts to generate the input files, run `input_file_writer.py` as follows:

```bash
COFFEE=<user-name> python input_file_writer.py <name-of-the-compound> <path-to-POSCAR-file>
```
Where `<user-name>` is the user directory of the person who is running the script and want the input files 
to be generated there, `<name-of-the-compound>` is the name of the compound you want to generate the input files for, 
and `<path-to-POSCAR-file>` is the path to the POSCAR file. The POSCAR file is a widely used format in 
[VASP](https://vasp.at/) software, which stores the lattice vectors and atomic positions for a given compound. 
The `input_file_writer.py` script will generate a folder named `<compound-name>`, and within that folder, it will create 
subfolders with the following directory structure:

```ansi
.
└── user_name/
    └── compound_name/
        ├── scf
        ├── projected_bands
        ├── pdos
        ├── strain
        └── spin_orbit/
            ├── scf
            ├── projected_bands
            ├── pdos
            └── wannier
```

After successfully executing `input_file_writer.py`, the input files will be created. Once you've done the usual calculations with Quantum ESPRESSO and Wannier90, you can run the `projected_bands_plotter.py` script using the following command:

```bash
COFFEE=<user-name> python projected_bands_plotter.py <compound-name>
```

After successfully executing `projected_bands_plotter.py`, the script will plot the projected bands for every atom in the structure.

To compare the wannier interpolated bands with DFT bands, run the following command:

```bash
COFFEE=<user-name> python compare_bands_plotter.py <compound-name>
```

## 🚧 Limitations

### 1- Projected Bands
The input file generation and plotting for projected bands currently only supports 2D hexagonal structures. You may need to modify the code to support other structures.

### 2- Atomic Projections
The software currently lacks whole atom projections for the projected bands and projected DOS (PDOS).

> ℹ️ Info
> 
> These limitations are due to the fact that the software is still in its early stages and is being actively developed. They are planned to be addressed in future releases.


## ⚙️ Configuration

### 1- Configuring Directory Structure and Input File Generation
If you want to customize the list of generated input files, you can do so by writing your own `config.json` file in 
`user_name` directory. The following keys in the `input` section are optional and can be removed if not needed:
- `relax_input`: The input file for Quantum ESPRESSO relax calculations
- `nscf_input`: The input file for Quantum ESPRESSO nscf calculations
- `pdos_input`: The input file for Quantum ESPRESSO pdos calculations
- `nscf_wannier_input`: The input file for Quantum ESPRESSO nscf calculations for usage in wannier90
- `pw2wan_input`: The input file for Quantum ESPRESSO pw2wannier90 calculations
- `wannier_input`: The input file for wannier90 calculations

The directory structure can also be modified by removing the following optional keys:
- `pdos`: The directory for pdos calculations
- `pdos_soc`: The directory for pdos calculations with spin-orbit coupling
- `wannier`: The directory for wannier calculations
- `wannier_soc`: The directory for wannier calculations with spin-orbit coupling
- `strain`: The directory for strain calculations

If you're not happy with the required keys, you can modify the `required_dirs` and `required_patterns` variables in the `config_validation.py` file. 
The `required_dirs` variable contains the list of required directories, while the `required_patterns` variable contains the list of required patterns 
for the input files.

The default config:
```json
{
  "directory_structure": {
    "scf": "scf",
    "scf_soc": "spin_orbit/scf",
    "projected_bands": "projected_bands",
    "projected_bands_soc": "spin_orbit/projected_bands",
    "pdos": "pdos",
    "pdos_soc": "spin_orbit/pdos",
    "wannier": "wannier",
    "wannier_soc": "spin_orbit/wannier",
    "strain": "strain",
    "pseudo": "../Pseudopotentials",
    "pseudo_rel": "../Pseudopotentials_rel"
  },
  "file_patterns": {
    "input": {
      "relax_input": "{compound_name}_relax{flag}.pw.in",
      "vc_relax_input": "{compound_name}_vc_relax{flag}.pw.in",
      "scf_input": "{compound_name}_scf{flag}.pw.in",
      "pw_bands_input": "{compound_name}_bands{flag}.pw.in",
      "kpdos_input": "{compound_name}{flag}.kpdos.in",
      "bands_input": "{compound_name}{flag}.bands.in",
      "nscf_input": "{compound_name}_nscf{flag}.pw.in",
      "pdos_input": "{compound_name}{flag}.pdos.in",
      "nscf_wannier_input": "{compound_name}_nscf_wannier{flag}.pw.in",
      "pw2wan_input": "{compound_name}{flag}.pw2wan.in",
      "wannier_input": "{compound_name}_wannier{flag}.win"
    },
    "output": {
      "relax_output": "{compound_name}_relax{flag}.pw.out",
      "vc_relax_output": "{compound_name}_vc_relax{flag}.pw.out",
      "scf_output": "{compound_name}_scf{flag}.pw.out",
      "pw_bands_output": "{compound_name}_bands{flag}.pw.out",
      "kpdos_output": "{compound_name}{flag}.kpdos.out",
      "projbands_output": "{compound_name}{flag}.projbands",
      "bands_gnu": "{compound_name}.bands.gnu",
      "nscf_output": "{compound_name}_nscf{flag}.pw.out"
    }
  }
}
```

An example of modified `config.json`:

```json
{
  "directory_structure": {
    "scf": "scf",
    "scf_soc": "spin_orbit/scf",
    "projected_bands": "projected_bands",
    "projected_bands_soc": "spin_orbit/projected_bands",
    "pdos": "pdos",
    "pdos_soc": "spin_orbit/pdos",
    "pseudo": "../Pseudopotentials",
    "pseudo_rel": "../Pseudopotentials_rel"
  },
  "file_patterns": {
    "input": {
      "vc_relax_input": "{compound_name}_vc_relax{flag}.pw.in",
      "scf_input": "{compound_name}_scf{flag}.pw.in",
      "pw_bands_input": "{compound_name}_bands{flag}.pw.in",
      "kpdos_input": "{compound_name}{flag}.kpdos.in",
      "bands_input": "{compound_name}{flag}.bands.in",
      "nscf_input": "{compound_name}_nscf{flag}.pw.in",
      "pdos_input": "{compound_name}{flag}.pdos.in"
    },
    "output": {
      "relax_output": "{compound_name}_relax{flag}.pw.out",
      "vc_relax_output": "{compound_name}_vc_relax{flag}.pw.out",
      "scf_output": "{compound_name}_scf{flag}.pw.out",
      "pw_bands_output": "{compound_name}_bands{flag}.pw.out",
      "kpdos_output": "{compound_name}{flag}.kpdos.out",
      "projbands_output": "{compound_name}{flag}.projbands",
      "bands_gnu": "{compound_name}.bands.gnu",
      "nscf_output": "{compound_name}_nscf{flag}.pw.out"
    }
  }
}
```

An example of the modified required sections in the `config_validation.py` file:

```python
required_dirs = {
    "scf",
    "scf_soc",
    "pdos",
    "pdos_soc",
    "pseudo",
    "pseudo_rel"
}

required_patterns = {
        "input": {
            "vc_relax_input",
            "scf_input",
            "nscf_input",
            "pdos_input",
        },
        "output": {
            "vc_relax_output",
            "scf_output",
            "pw_bands_output",
            "kpdos_output",
            "projbands_output",
            "bands_gnu"
        }
    }
```

### 2- Configuring Plot Settings
You can modify the plot settings by creating a `plot_config.yaml` file in the `user_name` directory.

The default config:
```yaml
# Bands plot configuration
bands_plot:
  high_symmetry_points: [ 0.0000, 0.5774, 0.9107, 1.5774 ] # Coordinates of high symmetry points in the Brillouin zone
  k_labels: [ "Gamma", "M", "K", "Gamma" ] # Labels for the high symmetry points
  orbital_colors:
    s: "#FF00ED"
    p: "#0BF317"
    d: "#FF2B11"
    pz: "#0D3EE0"
    "px+py": "#0BF317"
    dz2: "#0D3EE0"
    "dxz+dyz": "#0BF317"
    "dx2y2+dxy": "#FF2B11"
  figure:
    height: 6 # Height of the figure in inches
    width: 12 # Width of the figure in inches
    energy_limits: [ -5, 5 ] # Energy limits for the plot

# Density of States (DOS) plot configuration
dos_plot:
  orbital_colors:
    s: "#FF00ED"
    p: "#0BF317"
    d: "#FF2B11"
  figure:
    height: 6
    width: 12
    energy_limits: [ -5, 5 ]
```

An example of modified `plot_config.yaml` with changed energy limits:

```yaml
# Bands plot configuration
bands_plot:
  high_symmetry_points: [ 0.0000, 0.5774, 0.9107, 1.5774 ] # Coordinates of high symmetry points in the Brillouin zone
  k_labels: [ "Gamma", "M", "K", "Gamma" ] # Labels for the high symmetry points
  orbital_colors:
    s: "#FF00ED"
    p: "#0BF317"
    d: "#FF2B11"
    pz: "#0D3EE0"
    "px+py": "#0BF317"
    dz2: "#0D3EE0"
    "dxz+dyz": "#0BF317"
    "dx2y2+dxy": "#FF2B11"
  figure:
    height: 6 # Height of the figure in inches
    width: 12 # Width of the figure in inches
    energy_limits: [ -10, 5 ] # Energy limits for the plot

# Density of States (DOS) plot configuration
dos_plot:
  orbital_colors:
    s: "#FF00ED"
    p: "#0BF317"
    d: "#FF2B11"
  figure:
    height: 6
    width: 12
    energy_limits: [ -10, 5 ]
```

## 📄 License
This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🏅 Acknowledgements
- Special thanks to [Will McGugan](https://github.com/willmcgugan) for creating the awesome [Rich](https://github.com/Textualize/rich) library 
- `projwfc_to_bands.awk` script provided by [Quantum ESPRESSO](https://www.quantum-espresso.org)
- `kmesh.pl` script provided by [Wannier90](https://wannier.org/)
- Logo created with [Gemini](https://gemini.google.com)
- Badges created with [Shields.io](https://shields.io/)