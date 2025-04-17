"""Module for collecting data from Quantum ESPRESSO output files."""

from file_parser import *
from input_handler import get_atomic_states
from path_handler import prepare_paths

class SpinOrbitHandler:
    """
    A class to handle spin-orbit coupling (SOC) related logic, including skipping SOC cases
    and managing errors during data collection from Quantum ESPRESSO output files.

    Attributes:
        skip_soc (bool): Indicates whether SOC cases should be skipped automatically.
    """

    def __init__(self, skip_soc=False):
        """
        Initializes the SpinOrbitHandler with the option to skip SOC cases.

        Args:
            skip_soc (bool): Whether to skip SOC cases. Defaults to False.
        """
        self.skip_soc = skip_soc

    def should_skip(self, flag):
        """
        Determines if a given case should be skipped based on the SOC flag.

        Args:
            flag (str): The flag indicating whether the case involves SOC (e.g., "_soc").

        Returns:
            bool: True if the case should be skipped, False otherwise.
        """
        return self.skip_soc and flag == "_soc"

    def handle_error(self, flag):
        """
        Handles errors encountered during data collection. For SOC cases, it provides
        the user with the option to skip the case or exit the program. For non-SOC cases,
        the program exits immediately.

        Args:
            flag (str): The flag indicating whether the case involves SOC (e.g., "_soc").

        Returns:
            bool: True if the SOC case is skipped, False otherwise.

        Raises:
            SystemExit: If the user chooses not to skip the SOC case or if the error is
                        not related to SOC.
        """
        if flag != "_soc":
            exit(1) # Exit immediately for non spin-orbit cases

        if self.skip_soc:
            print("Spin-orbit was set to be skipped. Continuing...")
            return True

        skip_soc_input = input(
            'Do you want to skip spin-orbit case? Enter "yes" if you want to skip spin-orbit or "no" to quit the program: '
        ).lower()

        if skip_soc_input == "no":
            exit(1)
        return True

def collect_dft_data(paths, compound_name, flag, extractor_func, atom = None, orbital = None):
    """
    Collect data from Quantum ESPRESSO output files using a specified extractor function.

    Args:
        paths (dict): Dictionary containing file paths.
        compound_name (str): Name of the compound being analyzed.
        flag (str): Suffix for the file name (e.g., "_soc" or "").
        extractor_func (function): Function used to extract specific data from the file.
        atom (str): Atomic symbol
        orbital (str): Orbital type (e.g., "s", "p", "d")

    Returns:
        tuple: A tuple containing:
            - data (any): The extracted data if successful, or None if an error occurs.
            - success (bool): True if data extraction was successful, False otherwise.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the data cannot be extracted from the file or one of atom or orbital is not None.
    """
    try:
        # atom and orbital should either be both None or both not None
        match (atom is None, orbital is None):

            case (True, True):
                data = extractor_func(paths, compound_name, flag)
                return data, True

            case (True, False) | (False, True):
                raise ValueError(
                    """Both atom and orbital should be either None or not None.
                    If you want to extract atomic states, please provide both atom and orbital."""
                )

            case (False, False):
                data = extractor_func(paths, compound_name, flag, atom, orbital)
                return data, True

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return None, False


def collect_band_numbers(paths, compound_name, spin_orbit_flag, skip_soc=False):
    """
    Collect band numbers from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flag (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: List of band numbers
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    number_of_bands_list = []

    for path, flag in zip(paths["pw_bands_output_paths"], spin_orbit_flag):
        if soc_handler.should_skip(flag):
            continue

        data, success = collect_dft_data(path, compound_name, flag, extract_band_number)

        if not success:
            if soc_handler.handle_error(flag):
                return number_of_bands_list
        else:
            number_of_bands_list.append(data)

    return number_of_bands_list


def collect_fermi_energies(paths, compound_name, spin_orbit_flag, skip_soc=False):
    """
    Collect Fermi energies from Quantum ESPRESSO output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flag (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: List of Fermi energies
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    fermi_energy_list = []

    for path, flag in zip(paths["scf_output_paths"], spin_orbit_flag):

        if soc_handler.should_skip(flag):
            continue

        data, success = collect_dft_data(path, compound_name, flag, extract_fermi_energy)

        if not success:
            if soc_handler.handle_error(flag):
                return fermi_energy_list
        else:
            fermi_energy_list.append(data)

    return fermi_energy_list

def collect_number_of_atomic_states(paths, compound_name, spin_orbit_flag, skip_soc=False):
    """
    Collect the number of atomic states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flag (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: List of number of atomic states
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    number_of_atomic_states_list = []

    for path, flag in zip(paths["kpdos_output_paths"], spin_orbit_flag):
        if soc_handler.should_skip(flag):
            continue

        data, success = collect_dft_data(path, compound_name, flag, extract_number_of_atomic_states)

        if not success:
            if soc_handler.handle_error(flag):
                return number_of_atomic_states_list
        else:
            number_of_atomic_states_list.append(data)

    return number_of_atomic_states_list


def collect_atomic_states_info(paths, compound_name, spin_orbit_flag, skip_soc=False):
    """
    Collect the atomic info states from Quantum ESPRESSO KPDOS output files.

    Args:
        paths (dict): Dictionary of file paths
        compound_name (str): Name of the compound
        spin_orbit_flag (list): List of flags for spin-orbit coupling
        skip_soc (bool): Whether to skip spin-orbit coupling calculations

    Returns:
        list: A list of dictionaries containing the indices and orbital weights of each atomic state
    """
    soc_handler = SpinOrbitHandler(skip_soc)
    atomic_states_info_list = []

    atomic_projection_list = get_atomic_states()

    for path, flag in zip(paths["kpdos_output_paths"], spin_orbit_flag):

        atomic_states_info = {}
        if soc_handler.should_skip(flag):
            continue

        for atom, orbital in atomic_projection_list:
            data, success = collect_dft_data(path, compound_name, flag, extract_atomic_states_info, atom, orbital)

            if not success:
                if soc_handler.handle_error(flag):
                    break
            else:
                atomic_states_info.update(data)

        atomic_states_info_list.append(atomic_states_info)

    return atomic_states_info_list


def prepare_dft_info(init_config):
    """
    Prepare DFT (Density Functional Theory) information by extracting data from Quantum ESPRESSO output files.

    Args:
        init_config (dict): Initial configuration dictionary containing paths, compound name, and other settings.

    Returns:
        dict: Updated configuration dictionary with extracted DFT information.
    """
    # Determine which spin_orbit_flag to use
    if init_config["include_stress"]:
        # For strain analysis, we need one flag for each strain amount plus the base case
        spin_orbit_flag = ["" for _ in range(len(init_config["stress_amounts"]) + 1)] if init_config["stress_amounts"] else [""]
    else:
        spin_orbit_flag = ["", "_soc"]

    # Extracting band numbers
    number_of_bands_list = collect_band_numbers(
        init_config["paths"],
        init_config["compound_name"],
        spin_orbit_flag,
        init_config["paths"]["skip_soc"]
    )

    # Extracting Fermi energies
    fermi_energy_list = collect_fermi_energies(
        init_config["paths"],
        init_config["compound_name"],
        spin_orbit_flag,
        init_config["paths"]["skip_soc"]
    )

    # Extracting number of atomic states
    number_of_atomic_states_list = collect_number_of_atomic_states(
        init_config["paths"],
        init_config["compound_name"],
        spin_orbit_flag,
        init_config["paths"]["skip_soc"]
    )

    # Extracting atomic states information
    atomic_states_info_list = collect_atomic_states_info(
        init_config["paths"],
        init_config["compound_name"],
        spin_orbit_flag,
        init_config["paths"]["skip_soc"]
    )

    # Updating configuration
    init_config["number_of_bands"], init_config["number_of_bands_soc"] = number_of_bands_list
    init_config["fermi_energy"], init_config["fermi_energy_soc"] = fermi_energy_list
    init_config["number_of_atomic_states"], init_config["number_of_atomic_states_soc"] = number_of_atomic_states_list
    init_config["atomic_states_info"], init_config["atomic_states_info_soc"] = atomic_states_info_list

    return init_config


# Test to ensure the module works as expected
if __name__ == "__main__":
    config = prepare_paths()
    config = prepare_dft_info(config)
    print("DFT information prepared successfully.\n")
    print(f"Number of bands: {config['number_of_bands']}")
    print(f"Number of bands (SOC)): {config['number_of_bands_soc']}")
    print(f"Fermi energy: {config['fermi_energy']}")
    print(f"Fermi energy (SOC): {config['fermi_energy_soc']}")
    print(f"Number of atomic states: {config['number_of_atomic_states']}")
    print(f"Number of atomic states (SOC): {config['number_of_atomic_states_soc']}")

    print("\nAtomic states info:")
    for atomic_state, info in config["atomic_states_info"].items():
        print(f"{atomic_state}: {info}")

    print("\nAtomic states info (SOC):")
    for atomic_state, info in config["atomic_states_info_soc"].items():
        print(f"{atomic_state}: {info}")