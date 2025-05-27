import argparse
from dataclasses import dataclass
from sys import argv
from typing import List, Optional, Tuple
from abc import ABC, abstractmethod

from core.input_handler import get_pseudopotential_files
from core.project_setup import initialize_project
from data.fetch_atomic_info import get_atomic_weights
from data.models import ProjectSetup
from input.generators.kpoints import generate_k_points_section
from input.generators.sections import *
from input.user_prompts import prompt_nbands, prompt_kmesh
from ui.print_thanks import print_animated_ascii
from ui.ui_helpers import print_error, print_header, print_info, print_success, progress_track, console
from utils.file_parser import get_poscar_data


@dataclass
class PWCalculationConfig:
    """Configuration for PW.x calculations."""
    calc_type: str
    requires_bands: bool = False
    requires_ions_cell: bool = False
    cell_dofree: str = "ibrav"


@dataclass
class GenerationContext:
    """Context object containing all data needed for input generation."""
    project: ProjectSetup
    atomic_weights: List[float]
    pseudo_list: List[str]
    rel_pseudo_list: Optional[List[str]]
    atomic_positions: List[str]
    lattice_vectors: List[str]
    relativistic: bool = False


class WannierParams:
    """Simple parameter storage for Wannier calculations."""

    def __init__(self):
        self._normal_params = {}
        self._soc_params = {}

    def set_params(self, nbands: int, kmesh: Tuple[int, int, int], relativistic: bool):
        if relativistic:
            self._soc_params = {"nbands": nbands, "kmesh": kmesh}
        else:
            self._normal_params = {"nbands": nbands, "kmesh": kmesh}

    def get_params(self, relativistic: bool) -> Tuple[Optional[int], Optional[Tuple[int, int, int]]]:
        params = self._soc_params if relativistic else self._normal_params
        return params.get("nbands"), params.get("kmesh")


class InputGenerator(ABC):
    """Abstract base class for input file generators."""

    @abstractmethod
    def generate(self, context: GenerationContext, **kwargs) -> str:
        """Generate input file content."""
        pass

    @abstractmethod
    def get_required_params(self) -> List[str]:
        """Get list of required parameters for this generator."""
        pass


class PWCalculationGenerator(InputGenerator):
    """Generator for PW.x calculation input files."""

    # Configuration for different calculation types
    CONFIGS = {
        "relax": PWCalculationConfig("relax", requires_ions_cell=True),
        "vc-relax": PWCalculationConfig("vc-relax", requires_ions_cell=True),
        "scf": PWCalculationConfig("scf"),
        "nscf": PWCalculationConfig("nscf", requires_bands=True),
        "bands": PWCalculationConfig("bands", requires_bands=True),
    }

    def __init__(self, calc_type: str):
        if calc_type not in self.CONFIGS:
            valid_types = ", ".join(self.CONFIGS.keys())
            raise InputGenerationError(f"Invalid calculation type: {calc_type}. "
                                       f"Valid types are: {valid_types}")
        self.config = self.CONFIGS[calc_type]

    def generate(self, context: GenerationContext, **kwargs) -> str:
        """Generate PW.x input file."""
        # Get optional parameters
        kmesh = kwargs.get('kmesh')
        nbnds = kwargs.get('nbnds')

        # Generate CONTROL section
        pseudo_dir = (context.project.rel_pseudo_dir if context.relativistic
                      else context.project.pseudo_dir)

        content = generate_control_section(
            self.config.calc_type,
            pseudo_dir,
            context.project.project_dir,
            context.project.compound_name,
            relativistic=context.relativistic
        )

        # Generate SYSTEM section
        content += self._generate_system_section(context, nbnds)

        # Generate ELECTRONS section
        content += generate_electrons_section(relativistic=context.relativistic)

        # Add IONS and CELL sections if needed
        if self.config.requires_ions_cell:
            content += f"""&IONS
        /
        &CELL
            cell_dofree      = '{self.config.cell_dofree}'
        /
        """

        # Generate remaining sections
        content += self._generate_species_and_structure_sections(context)
        content += self._generate_kpoints_section(context, kmesh)

        return content

    def _generate_system_section(self, context: GenerationContext, nbnds: Optional[int]) -> str:
        """Generate SYSTEM section with band handling."""
        if not self.config.requires_bands:
            return generate_system_section(
                context.project.compound_data.number_of_atoms,
                context.project.compound_data.atom_types,
                relativistic=context.relativistic
            )

        # Handle bands requirement
        while True:
            try:
                if nbnds is None:
                    number_of_bands = prompt_nbands(self.config.calc_type, context.relativistic)
                else:
                    number_of_bands = nbnds

                return generate_system_section(
                    context.project.compound_data.number_of_atoms,
                    context.project.compound_data.atom_types,
                    number_of_bands=number_of_bands,
                    relativistic=context.relativistic
                )
            except ValueError as e:
                if nbnds is not None:  # If nbnds was provided but invalid, raise error
                    raise
                print_error("Error in generating SYSTEM section:")
                print_error(str(e))

    @staticmethod
    def _generate_species_and_structure_sections(context: GenerationContext) -> str:
        """Generate ATOMIC_SPECIES, ATOMIC_POSITIONS, and CELL_PARAMETERS sections."""
        pseudo_list = (context.rel_pseudo_list if context.relativistic
                       else context.pseudo_list)

        content = generate_atomic_species_section(
            context.project.compound_data.element_names,
            pseudo_list,
            context.atomic_weights
        )
        content += generate_atomic_positions_section(
            context.project.compound_data.atomic_labels,
            context.atomic_positions
        )
        content += generate_cell_parameters_section(context.lattice_vectors)

        return content

    def _generate_kpoints_section(self, context: GenerationContext, kmesh: Optional[Tuple[int, int, int]]) -> str:
        """Generate K_POINTS section with error handling."""
        while True:
            try:
                if self.config.calc_type != "bands":
                    if not kmesh:
                        k_mesh_density = prompt_kmesh(self.config.calc_type, context.relativistic)
                        return generate_k_points_section(self.config.calc_type, k_mesh_density)
                    else:
                        return generate_k_points_section(self.config.calc_type, kmesh, is_wannier=True)
                else:
                    return generate_k_points_section(self.config.calc_type)

            except ValueError as e:
                print_error("Error in generating K_POINTS section:")
                print_error(str(e))


            except InputGenerationError as e:
                print_error("Fatal Error in generating K_POINTS section:")
                print_error(str(e))
                exit(1)

    def get_required_params(self) -> List[str]:
        """Get required parameters for this calculation type."""
        params = []
        if self.config.requires_bands:
            params.append("nbnds")
        if self.config.calc_type != "bands":
            params.append("kmesh")
        return params


class PostProcessingGenerator(InputGenerator):
    """Generator for post-processing input files (PDOS, bands, etc.)."""

    GENERATORS = {
        "pdos": lambda compound_name, **kwargs: f"""&PROJWFC
    outdir          = './out'
    prefix          = '{compound_name}'
    filpdos         = '{compound_name}'
    DeltaE          = {kwargs.get('delta', 0.01)}
 /""",

        "kpdos": lambda compound_name, **kwargs: f"""&PROJWFC
    outdir       = './out'
    prefix       = '{compound_name}'
    DeltaE       = {kwargs.get('delta', 0.01)}
    kresolveddos = .true.
    filpdos      = '{compound_name}.k'
    lsym         = .false.
    filproj      = '{compound_name}.proj.dat'
/""",

        "bands": lambda compound_name, **kwargs: f"""&BANDS
    outdir       = './out'
    prefix       = '{compound_name}'
    filband      = '{compound_name}.bands'
    lsym         = .true.
    filband      = '{compound_name}.bands'
/"""
    }

    def __init__(self, post_type: str):
        if post_type not in self.GENERATORS:
            valid_types = ", ".join(self.GENERATORS.keys())
            raise InputGenerationError(f"Invalid post-processing type: {post_type}. "
                                     f"Valid types are: {valid_types}")
        self.post_type = post_type

    def generate(self, context: GenerationContext, **kwargs) -> str:
        """Generate post-processing input file."""
        return self.GENERATORS[self.post_type](context.project.compound_name, **kwargs)

    def get_required_params(self) -> List[str]:
        """Get required parameters."""
        return []  # Post-processing files typically don't require additional params


class WannierGenerator(InputGenerator):
    """Generator for Wannier90-related input files."""

    def __init__(self, wannier_input_type: str, wannier_params: WannierParams):
        self.wannier_type = wannier_input_type
        self.wannier_params = wannier_params

        valid_types = ["nscf_wannier", "pw2wan", "wannier"]
        if wannier_input_type not in valid_types:
            raise InputGenerationError(f"Invalid Wannier type: {wannier_input_type}. "
                                       f"Valid types are: {', '.join(valid_types)}")

    def generate(self, context: GenerationContext, **kwargs) -> str:
        """Generate Wannier-related input file."""
        if self.wannier_type == "nscf_wannier":
            return self._generate_nscf_wannier(context, **kwargs)
        elif self.wannier_type == "pw2wan":
            return self._generate_pw2wannier(context)
        elif self.wannier_type == "wannier":
            return self._generate_wannier_input(context, **kwargs)
        else:
            raise InputGenerationError(f"Unsupported Wannier type: {self.wannier_type}")

    def _generate_nscf_wannier(self, context: GenerationContext, **kwargs) -> str:
        """Generate NSCF input for Wannier calculations."""
        # Get stored parameters or prompt for new ones
        nbands = kwargs.get('nbnds')
        kmesh = kwargs.get('kmesh')

        if not nbands or not kmesh:
            while True:
                try:
                    if nbands is None:
                        nbands = prompt_nbands("wannier", context.relativistic)
                    if kmesh is None:
                        kmesh = prompt_kmesh("wannier", context.relativistic)

                    # Store parameters for later use
                    self.wannier_params.set_params(nbands, kmesh, context.relativistic)
                    break
                except ValueError as e:
                    print_error(f"Error in input: {str(e)}")
                    continue

        # Generate using PW calculator
        pw_gen = PWCalculationGenerator("nscf")
        return pw_gen.generate(context, nbnds=nbands, kmesh=kmesh)

    @staticmethod
    def _generate_pw2wannier(context: GenerationContext) -> str:
        """Generate pw2wannier90.x input file."""
        compound_name = context.project.compound_name

        content = f"""&inputpp
  outdir     =  './out'   ! quantum espresso outdir
  prefix     =  '{compound_name}' ! prefix of the pw.x scf calculation
  """

        if context.relativistic:
            content += f"  seedname   =  '{compound_name}_wannier_soc' ! must be same as the file name of win file"
        else:
            content += f"  seedname   =  '{compound_name}_wannier' ! must be same as the file name of win file"

        content += """
  write_amn  =  .true.
  write_mmn  =  .true.
/
"""
        return content

    def _generate_wannier_input(self, context: GenerationContext, **kwargs) -> str:
        """Generate Wannier90 input file."""
        # Get stored parameters
        nbands, kmesh = self.wannier_params.get_params(context.relativistic)

        # Allow override from kwargs
        nbands = kwargs.get('stored_nbands', nbands)
        kmesh = kwargs.get('stored_kmesh', kmesh)

        if nbands is None or kmesh is None:
            raise InputGenerationError("Wannier parameters not set. Generate nscf_wannier first.")

        num_iter = kwargs.get('num_iter', 250)
        dis_num_iter = kwargs.get('dis_num_iter', 2500)

        content = f"""num_bands = {nbands} ! number of bands
num_wann  = 0 ! Enter the number of wannier projections here
num_iter  = {num_iter} ! number of minimization iterations

! disentaglement
! Enter the appropriate energy windows here
dis_win_min  = 0 ! lower bound of bands to extract
dis_win_max  = 0 ! upper bound of bands to extract
!dis_froz_min = 0 ! lower bound of inner window
!dis_froz_max = 0 ! upper bound of innesr window
dis_num_iter = {dis_num_iter} ! number of disentanglement iterations

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
"""
        for element in context.project.compound_data.element_names:
            content += f"{element:<2}: proj\n"

        content += "end projections\n"

        if context.relativistic:
            content += f"""
! Required for spin orbit
spinors = true

begin unit_cell_cart
angstrom
"""
        else:
            content += """
begin unit_cell_cart
angstrom
"""

        for vector in context.lattice_vectors:
            content += f"    {vector}\n"

        content += """end unit_cell_cart

begin atoms_frac
"""

        for label, position in zip(context.project.compound_data.atomic_labels,
                                   context.atomic_positions):
            content += f"{label:<2}    {position}\n"

        content += f"""end atoms_frac

mp_grid = {kmesh[0]} {kmesh[1]} {kmesh[2]}

begin kpoints
"""
        content += generate_k_points_section("wannier", kmesh, is_wannier=True)
        content += "end kpoints\n"

        return content

    def get_required_params(self) -> List[str]:
        """Get required parameters."""
        if self.wannier_type == "nscf_wannier":
            return ["nbnds", "kmesh"]
        return []


class InputGeneratorFactory:
    """Factory for creating input file generators."""

    def __init__(self):
        self.wannier_params = WannierParams()

    def create_generator(self, input_type: str) -> InputGenerator:
        """Create appropriate generator based on input type."""

        # PW calculations
        if input_type in ["relax", "vc-relax", "scf", "nscf", "bands"]:
            return PWCalculationGenerator(input_type)

        # Post-processing
        elif input_type in ["pdos", "kpdos", "pw_bands"]:
            post_type = input_type.replace("pw_", "")  # Handle pw_bands -> bands
            return PostProcessingGenerator(post_type)

        # Wannier-related
        elif input_type in ["nscf_wannier", "pw2wan", "wannier"]:
            return WannierGenerator(input_type, self.wannier_params)

        else:
            raise InputGenerationError(f"Unknown input type: {input_type}")


class InputFileManager:
    """High-level manager for input file generation and writing."""

    def __init__(self, project: ProjectSetup):
        self.project = project
        self.factory = InputGeneratorFactory()
        self._context = None

    def initialize_context(self) -> GenerationContext:
        """Initialize the generation context with all required data."""
        print_info("Fetching atomic weights and POSCAR data...")

        with console.status("Retrieving atomic weights and POSCAR data"):
            atomic_weights = get_atomic_weights(self.project.compound_data.element_names)
            lattice_vectors, atomic_positions = get_poscar_data(self.project.poscar_file)

        print_info("Fetching the Pseudopotentials...")
        pseudo_list, rel_pseudo_list = get_pseudopotential_files(
            self.project.compound_data.element_names,
            self.project.pseudo_dir,
            relativistic=True,
            rel_pseudo_path=self.project.rel_pseudo_dir
        )
        print_info("Pseudopotentials fetched successfully.")

        self._context = GenerationContext(
            project=self.project,
            atomic_weights=atomic_weights,
            pseudo_list=pseudo_list,
            rel_pseudo_list=rel_pseudo_list,
            atomic_positions=atomic_positions,
            lattice_vectors=lattice_vectors
        )

        return self._context

    def generate_input_file(self, input_type: str, relativistic: bool = False, **kwargs) -> str:
        """Generate a single input file."""
        if self._context is None:
            self.initialize_context()

        # Update context for relativistic calculation
        context = GenerationContext(
            project=self._context.project,
            atomic_weights=self._context.atomic_weights,
            pseudo_list=self._context.pseudo_list,
            rel_pseudo_list=self._context.rel_pseudo_list,
            atomic_positions=self._context.atomic_positions,
            lattice_vectors=self._context.lattice_vectors,
            relativistic=relativistic
        )

        generator = self.factory.create_generator(input_type)
        return generator.generate(context, **kwargs)

    def write_all_input_files(self, skip_soc: bool = False) -> None:
        """Write all input files for the project."""
        if self._context is None:
            self.initialize_context()

        print_info("Starting input file generation...\n")
        print_header("Input File Generation")

        generated_files = []

        print_info("Generating input files...")
        for key, paths in self.project.input_paths.items():
            input_type = key.replace("_paths", "").replace("_input", "")

            try:
                generator = self.factory.create_generator(input_type)
            except InputGenerationError:
                continue  # Skip unknown input types

            if not self.project.include_stress:
                # Generate both normal and SOC versions
                for path, relativistic in zip(paths, [False, True]):
                    file_name = os.path.basename(path)

                    if "_soc" in file_name and skip_soc:
                        print_info(f"Skipping SOC file generation for {file_name}")
                        continue

                    context = GenerationContext(
                        project=self._context.project,
                        atomic_weights=self._context.atomic_weights,
                        pseudo_list=self._context.pseudo_list,
                        rel_pseudo_list=self._context.rel_pseudo_list,
                        atomic_positions=self._context.atomic_positions,
                        lattice_vectors=self._context.lattice_vectors,
                        relativistic=relativistic
                    )

                    try:
                        content = generator.generate(context)
                        generated_files.append((file_name, path, content))
                    except Exception as e:
                        print_error(f"Error generating {file_name}: {str(e)}")
                        continue
            else:
                # Generate only normal version
                for path in paths:
                    file_name = os.path.basename(path)

                    context = GenerationContext(
                        project=self._context.project,
                        atomic_weights=self._context.atomic_weights,
                        pseudo_list=self._context.pseudo_list,
                        rel_pseudo_list=self._context.rel_pseudo_list,
                        atomic_positions=self._context.atomic_positions,
                        lattice_vectors=self._context.lattice_vectors,
                        relativistic=False
                    )

                    try:
                        content = generator.generate(context)
                        generated_files.append((file_name, path, content))
                    except Exception as e:
                        print_error(f"Error generating {file_name}: {str(e)}")
                        continue

        print_success("\nInput files have been generated successfully.\n")
        print_header("Writing Input Files")

        for file_name, path, content in progress_track(generated_files, description="Writing input files"):
            try:
                with open(path, "w") as f:
                    f.write(content)
                print_success(f"Wrote {file_name} at:\n    {path}")
            except Exception as e:
                print_error(f"Error writing {file_name}: {str(e)}")

        print_success("All input files have been written successfully.")
        print_animated_ascii("ascii-art.txt")
        console.print("\nThanks for using Quantum Instant Coffee :)", style="bold cyan")


if __name__ == "__main__":
    """
    Main entry point for the script.

    This block initializes the project, retrieves necessary data, and generates
    the NSCF input file for Quantum ESPRESSO calculations. It performs the following steps:
    1. Determines if the script is called for input file generation.
    2. Initializes the project setup using command-line arguments.
    3. Retrieves pseudopotential files for the specified elements.
    4. Fetches atomic weights and POSCAR data (lattice vectors and atomic positions).
    5. Generates the NSCF input file using the provided data and configuration.
    6. Prints the generated NSCF input file content.
    """
    # Create the parser
    parser = argparse.ArgumentParser(description="Writes input files for Quantum ESPRESSO and Wannier90 calculations.")

    # Add arguments
    parser.add_argument(
        "compound_name",
        type=str,
        help="Name of the compound (e.g., 'GaAs', 'SiO2')."
    )
    parser.add_argument(
        "poscar_file",
        type=str,
        help="Path to the POSCAR file."
    )

    # Parse the arguments
    args = parser.parse_args(argv[1:])
    compound_name, poscar_file = args.compound_name, args.poscar_file

    os.chdir("../..")

    project = initialize_project(compound_name, poscar_file=poscar_file, is_input=True)

    manager = InputFileManager(project)

    try:
        nscf_input = manager.generate_input_file("nscf", relativistic=True)
        print_info(nscf_input)
    except Exception as e:
        print_error(f"Error generating NSCF input: {str(e)}")