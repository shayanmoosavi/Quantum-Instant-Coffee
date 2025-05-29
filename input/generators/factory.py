"""Input File Generation Module

This module provides classes and data structures for generating input files
for Quantum ESPRESSO and Wannier90 calculations. It includes configurations
for different calculation types, context management for input generation,
and parameter storage for Wannier calculations.
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from abc import ABC, abstractmethod

from data.models import ProjectSetup
from input.generators.kpoints import generate_k_points_section
from input.generators.sections import *
from input.user_prompts import prompt_nbands, prompt_kmesh
from ui.ui_helpers import print_error


@dataclass
class PWCalculationConfig:
    """
    Configuration for PW.x calculations.

    Attributes:
        calc_type (str): Type of calculation (e.g., "relax", "scf", "bands").
        requires_bands (bool): Whether the calculation requires band information.
        requires_ions_cell (bool): Whether the calculation requires IONS and CELL sections.
        cell_dofree (str): Degree of freedom for cell optimization. Defaults to "ibrav".
    """
    calc_type: str
    requires_bands: bool = False
    requires_ions_cell: bool = False
    cell_dofree: str = "ibrav"


@dataclass
class GenerationContext:
    """
    Context object containing all data needed for input generation.

    Attributes:
        project (ProjectSetup): Project setup information.
        atomic_weights (List[float]): List of atomic weights for the compound.
        pseudo_list (List[str]): List of pseudopotential file paths.
        rel_pseudo_list (Optional[List[str]]): List of relativistic pseudopotential file paths.
        atomic_positions (List[str]): List of atomic positions in fractional coordinates.
        lattice_vectors (List[str]): List of lattice vectors in Cartesian coordinates.
        relativistic (bool): Whether the calculation is relativistic (SOC). Defaults to False.
    """
    project: ProjectSetup
    atomic_weights: List[float]
    pseudo_list: List[str]
    rel_pseudo_list: Optional[List[str]]
    atomic_positions: List[str]
    lattice_vectors: List[str]
    relativistic: bool = False


class WannierParams:
    """
    Simple parameter storage for Wannier calculations.

    Attributes:
        _normal_params (dict): Parameters for non-relativistic calculations.
        _soc_params (dict): Parameters for relativistic calculations.
    """

    def __init__(self):
        """
        Initializes the WannierParams object with empty parameter dictionaries.
        """
        self._normal_params = {}
        self._soc_params = {}

    def set_params(self, nbands: int, kmesh: Tuple[int, int, int], relativistic: bool):
        """
        Sets the parameters for Wannier calculations.

        Args:
            nbands (int): Number of bands.
            kmesh (Tuple[int, int, int]): K-point mesh density.
            relativistic (bool): Whether the calculation is relativistic (SOC).
        """
        if relativistic:
            self._soc_params = {"nbands": nbands, "kmesh": kmesh}
        else:
            self._normal_params = {"nbands": nbands, "kmesh": kmesh}

    def get_params(self, relativistic: bool) -> Tuple[Optional[int], Optional[Tuple[int, int, int]]]:
        """
        Retrieves the stored parameters for Wannier calculations.

        Args:
            relativistic (bool): Whether to retrieve parameters for relativistic calculations.

        Returns:
            Tuple[Optional[int], Optional[Tuple[int, int, int]]]: Number of bands and K-point mesh density.
        """
        params = self._soc_params if relativistic else self._normal_params
        return params.get("nbands"), params.get("kmesh")


class InputGenerator(ABC):
    """
    Abstract base class for input file generators.

    This class defines the interface for input file generators, ensuring that
    all derived classes implement the required methods for generating input
    file content and retrieving required parameters.
    """

    @abstractmethod
    def generate(self, context: GenerationContext, **kwargs) -> str:
        """
        Generate input file content.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.
            **kwargs: Additional parameters specific to the input file generation.

        Returns:
            str: The generated input file content.
        """
        pass

    @abstractmethod
    def get_required_params(self) -> List[str]:
        """
        Get the list of required parameters for this generator.

        Returns:
            List[str]: A list of parameter names required for input file generation.
        """
        pass


class PWCalculationGenerator(InputGenerator):
    """
    Generator for PW.x calculation input files.

    This class handles the generation of input files for different types of PW.x
    calculations, such as 'relax', 'scf', 'nscf', and 'bands'. It uses predefined
    configurations for each calculation type.
    """

    # Configuration for different calculation types
    CONFIGS = {
        "relax": PWCalculationConfig("relax", requires_ions_cell=True),
        "vc-relax": PWCalculationConfig("vc-relax", requires_ions_cell=True),
        "scf": PWCalculationConfig("scf"),
        "nscf": PWCalculationConfig("nscf", requires_bands=True),
        "bands": PWCalculationConfig("bands", requires_bands=True),
    }

    def __init__(self, calc_type: str):
        """
        Initialize the PWCalculationGenerator with the specified calculation type.

        Args:
            calc_type (str): The type of calculation (e.g., 'relax', 'scf', 'bands').

        Raises:
            InputGenerationError: If the provided calculation type is invalid.
        """
        if calc_type not in self.CONFIGS:
            valid_types = ", ".join(self.CONFIGS.keys())
            raise InputGenerationError(f"Invalid calculation type: {calc_type}. "
                                       f"Valid types are: {valid_types}")
        self.config = self.CONFIGS[calc_type]

    def generate(self, context: GenerationContext, **kwargs) -> str:
        """
        Generate the PW.x input file content.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.
            **kwargs: Additional parameters such as 'kmesh' and 'nbnds'.

        Returns:
            str: The generated input file content.
        """
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
        """
        Generate the SYSTEM section of the input file.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.
            nbnds (Optional[int]): The number of bands, if required.

        Returns:
            str: The SYSTEM section content.
        """
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
        """
        Generate the ATOMIC_SPECIES, ATOMIC_POSITIONS, and CELL_PARAMETERS sections.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.

        Returns:
            str: The content of the species and structure sections.
        """
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
        """
        Generate the K_POINTS section of the input file.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.
            kmesh (Optional[Tuple[int, int, int]]): The K-point mesh density.

        Returns:
            str: The K_POINTS section content.

        Raises:
            ValueError: If the K-point mesh density is invalid.
            InputGenerationError: If there is a fatal error in generating the K_POINTS section.
        """
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
        """
        Get the list of required parameters for this calculation type.

        Returns:
            List[str]: A list of parameter names required for input file generation.
        """
        params = []
        if self.config.requires_bands:
            params.append("nbnds")
        if self.config.calc_type != "bands":
            params.append("kmesh")
        return params


class PostProcessingGenerator(InputGenerator):
    """
    Generator for post-processing input files (PDOS, bands, etc.).

    Attributes:
        GENERATORS (dict): A dictionary mapping post-processing types to lambda functions
                           that generate the corresponding input file content.
    """

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
        """
        Initializes the PostProcessingGenerator with the specified post-processing type.

        Args:
            post_type (str): The type of post-processing (e.g., 'pdos', 'kpdos', 'bands').

        Raises:
            InputGenerationError: If the provided post-processing type is invalid.
        """
        if post_type not in self.GENERATORS:
            valid_types = ", ".join(self.GENERATORS.keys())
            raise InputGenerationError(f"Invalid post-processing type: {post_type}. "
                                     f"Valid types are: {valid_types}")
        self.post_type = post_type

    def generate(self, context: GenerationContext, **kwargs) -> str:
        """
        Generates the post-processing input file content.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.
            **kwargs: Additional parameters specific to the post-processing type.

        Returns:
            str: The generated input file content.
        """
        return self.GENERATORS[self.post_type](context.project.compound_name, **kwargs)

    def get_required_params(self) -> List[str]:
        """
        Retrieves the list of required parameters for this generator.

        Returns:
            List[str]: An empty list, as post-processing files typically don't require additional parameters.
        """
        return []


class WannierGenerator(InputGenerator):
    """
    Generator for Wannier90-related input files.

    Attributes:
        wannier_type (str): The type of Wannier input file to generate (e.g., 'nscf_wannier', 'pw2wan', 'wannier').
        wannier_params (WannierParams): An object for storing and retrieving Wannier calculation parameters.
    """

    def __init__(self, wannier_input_type: str, wannier_params: WannierParams):
        """
        Initializes the WannierGenerator with the specified input type and parameters.

        Args:
            wannier_input_type (str): The type of Wannier input file to generate.
            wannier_params (WannierParams): An object for storing and retrieving Wannier calculation parameters.

        Raises:
            InputGenerationError: If the provided Wannier input type is invalid.
        """
        self.wannier_type = wannier_input_type
        self.wannier_params = wannier_params

        valid_types = ["nscf_wannier", "pw2wan", "wannier"]
        if wannier_input_type not in valid_types:
            raise InputGenerationError(f"Invalid Wannier type: {wannier_input_type}. "
                                       f"Valid types are: {', '.join(valid_types)}")

    def generate(self, context: GenerationContext, **kwargs) -> str:
        """
        Generates the Wannier-related input file content.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.
            **kwargs: Additional parameters specific to the Wannier input type.

        Returns:
            str: The generated input file content.

        Raises:
            InputGenerationError: If the Wannier input type is unsupported.
        """
        if self.wannier_type == "nscf_wannier":
            return self._generate_nscf_wannier(context, **kwargs)
        elif self.wannier_type == "pw2wan":
            return self._generate_pw2wannier(context)
        elif self.wannier_type == "wannier":
            return self._generate_wannier_input(context, **kwargs)
        else:
            raise InputGenerationError(f"Unsupported Wannier type: {self.wannier_type}")

    def _generate_nscf_wannier(self, context: GenerationContext, **kwargs) -> str:
        """
        Generates NSCF input for Wannier calculations.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.
            **kwargs: Additional parameters such as 'nbnds' and 'kmesh'.

        Returns:
            str: The generated NSCF input file content.
        """
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
        """
        Generates pw2wannier90.x input file content.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.

        Returns:
            str: The generated pw2wannier90.x input file content.
        """
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
        """
        Generates Wannier90 input file content.

        Args:
            context (GenerationContext): The context containing all necessary data for input generation.
            **kwargs: Additional parameters such as 'stored_nbands', 'stored_kmesh', 'num_iter', and 'dis_num_iter'.

        Returns:
            str: The generated Wannier90 input file content.

        Raises:
            InputGenerationError: If required Wannier parameters are not set.
        """
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
        """
        Retrieves the list of required parameters for this generator.

        Returns:
            List[str]: A list of required parameters, depending on the Wannier input type.
        """
        if self.wannier_type == "nscf_wannier":
            return ["nbnds", "kmesh"]
        return []


class InputGeneratorFactory:
    """
    Factory for creating input file generators.

    Attributes:
        wannier_params (WannierParams): An object for storing and retrieving Wannier calculation parameters.
    """

    def __init__(self):
        """
        Initializes the InputGeneratorFactory with a WannierParams object.
        """
        self.wannier_params = WannierParams()

    def create_generator(self, input_type: str) -> InputGenerator:
        """
        Creates an appropriate generator based on the input type.

        Args:
            input_type (str): The type of input file to generate (e.g., 'relax', 'pdos', 'wannier').

        Returns:
            InputGenerator: The corresponding generator for the specified input type.

        Raises:
            InputGenerationError: If the input type is unknown.
        """

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
