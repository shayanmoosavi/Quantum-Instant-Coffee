# Quantum Instant Coffee ![Static Badge](https://img.shields.io/badge/Input%20file%20generator-red) ![Static Badge](https://img.shields.io/badge/Easy%20plotting-red) ![Static Badge](https://img.shields.io/badge/Preprocessing-red) ![Static Badge](https://img.shields.io/badge/Postprocessing-red)
> An instant input file generator and plotting scripts for Quantum ESPRESSO and Wannier90

<div align="center">
<img src="Logo.png" align="center"/>
</div>

## 💡 About
Quantum Instant Coffee is a collection of Python scripts designed to easily generate batches of input files needed for the most common [Quantum ESPRESSO](https://www.quantum-espresso.org) and [Wannier90](https://wannier.org/) calculations. The current supported calculations include:

- **Self-Consistent Field** (scf)
- **Projected Density of States** (pdos)
- **Projected Band Structure** (projected_bands)
- **Wannier interpolated bands** (wannier)

The input files will be generated both with and without considering spin-orbit coupling and will be organized into their respective directories.

Current toolkit:
- `init_calc.py`
- `plot_pbands.py`
- `plot_pdos.py` (coming soon)
- `compare_bands.py` (coming soon)

## 📖 Usage
In order to use these scripts to generate the input files, first clone the repository into the main directory where you want to generate input files. Then, run `init_calc.py` as follows:

```bash
python init_calc.py <name-of-the-compound> <path-to-POSCAR-file>
```

The POSCAR file is a widely used format in [VASP](https://vasp.at/) software, which stores the lattice vectors and atomic positions for a given compound. The `init_calc.py` script will generate a folder named `<name-of-the-compound>`, and within that folder, it will create subfolders with the following structure:

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

After successfully executing `init_calc.py`, the input files will be mostly ready. The only information missing is the pseudopotential files and atomic weights, which need to be added manually in the input scripts. Once you've done the usual calculations with Quantum ESPRESSO and Wannier90, you can run the `plot_pbands.py` script using the following command:

```bash
python plot_pbands.py <name-of-the-compound>
```

After successfully exwcuting `plot_pbands.py`, the script will plot the projected bands for every atom in the structure.

## 🏅 Acknowledgements
- Logo created with [Banner Maker](https://banner.godori.dev/)
- Badges created with [Shields.io](https://shields.io/)
- Logo icon provided by [Flaticon](https://www.flaticon.com/)
