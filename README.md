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
