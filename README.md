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

The input files will be generated both with and without considering spin-orbit coupling, with files organized in a clear directory structure.

### 🧰 Toolkit:
- `input_file_writer.py`: Generates input files for common QE/Wannier90 workflows
- `plotter.py`: Visualizes results from QE and Wannier90 calculations, including:
  - Projected band structure
  - Projected density of states (PDOS)
  - Comparison of DFT vs Wannier interpolated bands

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

Or alternatively, download the latest release from the releases section of the repository.

### 2 - Install the required packages
To install the required packages, you can use pip.

For all the dependencies:
```bash
pip install numpy matplotlib pandas rich pyyaml beautifulsoup4 requests lxml
```

For the required packages:
```bash
pip install numpy matplotlib pandas rich pyyaml
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
- PDOS visualization with orbital-specific contributions
- Comparative analysis of DFT vs Wannier interpolated bands

## 🔍 Troubleshooting

### Missing Pseudopotentials
If you encounter errors about missing pseudopotentials, ensure you have:
1. Downloaded the appropriate pseudopotential files
2. Updated the paths in the generated input files

## 📖 Usage
In order to use these scripts to generate the input files, run `input_file_writer.py` as follows:

```bash
COFFEE=<user-name> python input_file_writer.py --project-config /path/to/project_congig.json <compound-name> <POSCAR-file> <config-type>
```

### Arguments
- `<user-name>`: The user directory of the person who is running the script and want the input files to be generated there
- `<compound-name>`: The name of the compound you want to generate the input files for (e.g., 'GaAs', 'SiO2')
- `<POSCAR-file>`: The path to the POSCAR file containing lattice vectors and atomic positions
- `<config-type>`: Type of configuration to use. Choose from:
  - `default`: Complete workflow including all calculation types
  - `bands`: Band structure calculations only
  - `pdos`: Projected density of states calculations only
  - `wannier`: Wannier function calculations only
- `--project-config` (optional): Path to a custom JSON project configuration file

You can also set the `COFFEE` environment variable before running the script, which will be used as the user name for the directory structure.

```bash
export COFFEE=<user-name>
python input_file_writer.py <compound-name> <POSCAR-file> <config-type>
```

### Examples
```bash
# Generate input files for all calculation types (default configuration)
python input_file_writer.py GaAs /path/to/POSCAR default

# Generate input files for band structure calculations only
python input_file_writer.py SiO2 ./structures/SiO2_POSCAR bands

# Use a custom project configuration file
python input_file_writer.py InAs POSCAR_InAs default --project-config my_config.json
```

The POSCAR file is a widely used format in [VASP](https://vasp.at/) software, which stores the lattice vectors and atomic positions 
for a given compound.

### Directory Structure
The `input_file_writer.py` script will generate a directory tree `user_name/compound_name`, and within that directory, 
it will create subdirectories based on the selected configuration type:

#### Default Configuration
```ansi
.
└── user_name/
    └── compound_name/
        ├── scf
        ├── projected_bands
        ├── pdos
        ├── wannier
        ├── strain
        └── spin_orbit/
            ├── scf
            ├── projected_bands
            ├── pdos
            └── wannier
```
#### Bands Configuration
```ansi
.
└── user_name/
    └── compound_name/
        ├── scf
        ├── projected_bands
        └── spin_orbit/
            ├── scf
            └── projected_bands
```
#### PDOS Configuration
```ansi
.
└── user_name/
    └── compound_name/
        ├── scf
        ├── pdos
        └── spin_orbit/
            ├── scf
            └── pdos
```
#### Wannier Configuration
```ansi
.
└── user_name/
    └── compound_name/
        ├── scf
        ├── projected_bands
        ├── wannier
        └── spin_orbit/
            ├── scf
            ├── projected_bands
            └── wannier
```

The script also references pseudopotential directories:

- `../Pseudopotentials/`: For standard pseudopotential files
- `../Pseudopotentials_rel/`: For relativistic pseudopotential files

After successfully executing `input_file_writer.py`, the input files will be created. Once you've done the usual calculations 
with Quantum ESPRESSO and Wannier90, you can run the `plotter.py` script using the following command:

```bash
COFFEE=<user-name> python plotter.py <compound-name> <plot-type>
```
Where `<plot-type>` is one of the following:
- `pdos`: Plots the projected density of states (PDOS)
- `bands`: Plots the projected band structure
- `wannier`: Compares the DFT bands with Wannier interpolated bands

You can also provide optional arguments to the `plotter.py` script:

```bash
COFFEE=<user-name> python plotter.py --plot-config /path/to/plot_config.yaml --save-fig <compound-name> <plot-type>
```

Where `--plot-config` is the path to the custom user-defined plot configuration file, which will be explained in the
[Configuration](#-configuration) section, and `--save-fig` is a flag to save the figure instead of displaying it.


## 🚧 Limitations

### 1- Projected Bands
The input file generation and plotting for projected bands currently only supports 2D hexagonal structures. You may need to modify the code to support other structures.

> [!NOTE]
> These limitations are due to the fact that the software is still in its early stages and is being actively developed. They are planned to be addressed in future releases.

### 2- Python Version
> [!WARNING]
> The software has been tested on Python 3.10. If you are using an older version of Python and encounter issues, open an issue on GitHub and I try to address it.

### 3- Operating System
> [!WARNING]
> The software has only been tested on Linux. If you are using Windows or MacOS and encounter issues, open an issue on GitHub and I try to address it.

If you have experience in developing for these platforms and would like to contribute and add better support for platforms other than Linux, please feel free 
to submit a pull request.

## ⚙️ Configuration

### 1- Configuring Directory Structure and Input File Generation
If you want to customize the list of generated input files, you can do so by writing your own `project_config.json` file in 
`user_name` directory. For example, you can remove the soc related directories if you don't need the 
relativistic calculations. However, you must pay attention to the required keys in the `config_validatoin.py` file. The default
configuration types are defined in `project_config.py` file, which contains the default directory structure and file patterns for input and output files.
It supports four config types of `default`, `bands`, `pdos`, and `wannier`. The `default` config type includes all the necessary directories and file patterns 
for all calculations, while the other three config types only include the necessary directories and file patterns for their respective calculations. For example, 
the `bands` config type only includes the directories and file patterns for the band structure calculations, while the `pdos` config type only includes the directories 
and file patterns for the projected density of states calculations.

If you're not happy with the required keys, you can modify the `required_dirs` and `required_patterns` variables in the `config_validation.py` file. 
The `required_dirs` variable contains the list of required directories, while the `required_patterns` variable contains the list of required patterns 
for the input files.

The default `project_config.json`
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

An example of modified `project_config.json`:

```json
{
  "directory_structure": {
    "scf": "scf",
    "projected_bands": "projected_bands",
    "pdos": "pdos",
    "pseudo": "../Pseudopotentials"
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
    s: "#FF00ED" # Magenta
    p: "#0BF317" # Green
    d: "#FF2B11" # Red
    pz: "#0D3EE0" # Blue
    "px+py": "#0BF317" # Green
    dz2: "#0D3EE0" # Blue
    "dxz+dyz": "#0BF317" # Green
    "dx2y2+dxy": "#FF2B11" # Red
    all: "#FBFF2F" # Yellow
  figure:
    height: 6 # Height of the figure in inches
    width: 12 # Width of the figure in inches
    energy_limits: [ -5, 5 ] # Energy limits for the plot

# Density of States (DOS) plot configuration
dos_plot:
  orbital_colors:
    s: "#FF00ED" # Magenta
    p: "#0BF317" # Green
    d: "#FF2B11" # Red
    all: "#FBFF2F" # Yellow
  figure:
    height: 6
    width: 12
  plot:
    energy_limits: [ -5, 5 ]
    dos_limits: [ 0, 10 ] # Limits for the DOS plot
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
  plot:
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
  plot:
    energy_limits: [ -10, 5 ]
    dos_limits: [ 0, 10 ] # Limits for the DOS plot
```

You can also provide partial configurations in the `plot_config.yaml` file. The script will use the default values for any missing keys. 
To provide a partial configuration, simply include the keys you want to modify, along with the plot type you want to modify.

For example, if you want to change the energy limits for the bands plot, you can create a `plot_config.yaml` file with the following content:

```yaml
bands_plot:
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