# Quantum Instant Coffee ![Static Badge](https://img.shields.io/badge/Input%20file%20generator-red) ![Static Badge](https://img.shields.io/badge/Easy%20plotting-red) ![Static Badge](https://img.shields.io/badge/Preprocessing-red) ![Static Badge](https://img.shields.io/badge/Postprocessing-red)
> An instant input file generator and plotting scripts for Quantum ESPRESSO and Wannier90

<div align="center">
<img src="Logo.png" align="center"/>
</div>

## 💡 About
Quantum Instant Coffee is a collection of Python scripts to easily generate a batch of all the needed input files for the most common [Quantum ESPRESSO](https://www.quantum-espresso.org) and [Wannier90](https://wannier.org/) calculations. The current supported calculations are:

- **Self-Consistent Field** (scf)
- **Projected Density of States** (pdos)
- **Projected Band Structure** (projected_bands)
- **Wannier interpolated bands** (wannier)

The input files will be generated with and without taking spin-orbit coupling into account and they will be placed in their respective directories.

Current toolkit:
- `init_calc.py`
- `plot_pbands.py`
- `plot_pdos.py` (coming soon)
- `compare_bands.py` (coming soon)

## 📖 Usage
In order to use these scripts to generate the input files, you must first clone the repository in the main directory you want to generate input files. Then, run `init_calc.py` in the following way:

```bash
python init_calc.py <name-of-the-compound> <path-to-POSCAR-file>
```
POSCAR is a famous file format generally used by the [VASP](https://vasp.at/) software , which stores the lattice vectors and the atomic positions for a specified compound. The script will generate a folder named `<name-of-the-compound>` and in that folder it will create subfolders with the following structure:

```bash
.
├── pdos
│   ├── <name-of-the-compound>_nscf.pw.in
│   └── <name-of-the-compound>.pdos.in
├── projected_bands
│   ├── <name-of-the-compound>.bands.in
│   ├── <name-of-the-compound>_bands.pw.in
│   └── <name-of-the-compound>.kpdos.in
├── scf
│   ├── <name-of-the-compound>_scf.pw.in
│   └── <name-of-the-compound>_vc_relax.pw.in
├── spin_orbit
│   ├── pdos
│   │   ├── <name-of-the-compound>_nscf_soc.pw.in
│   │   └── <name-of-the-compound>_soc.pdos.in
│   ├── projected_bands
│   │   ├── <name-of-the-compound>_bands_soc.pw.in
│   │   ├── <name-of-the-compound>_soc.bands.in
│   │   └── <name-of-the-compound>_soc.kpdos.in
│   ├── scf
│   │   ├── <name-of-the-compound>_scf_soc.pw.in
│   │   └── <name-of-the-compound>_vc_relax_soc.pw.in
│   └── wannier
│       ├── <name-of-the-compound>_nscf_wannier_soc.pw.in
│       ├── <name-of-the-compound>_soc.pw2wan.in
│       └── <name-of-the-compound>_wannier_soc.win
└── wannier
├── <name-of-the-compound>_nscf_wannier.pw.in
├── <name-of-the-compound>.pw2wan.in
└── <name-of-the-compound>_wannier.win
```
