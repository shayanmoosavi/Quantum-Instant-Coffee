""" Module for extracting data from Quantum ESPRESSO output files.

This module provides functionality for extracting data from Quantum ESPRESSO
output files. It includes abstract base classes and specific implementations
for extracting various types of data, such as atomic states and Wannier parameters.

Classes:
    DataExtractor: Abstract base class defining the interface for data extraction strategies.
    SimpleDataExtractor: Extractor for single value extraction using a specified function.
    AtomicStatesExtractor: Extractor for atomic states information, including orbital weights and indices.
    WannierDataExtractor: Extractor for Wannier parameters (alat and Fermi energy).

Functions:
    collect_dft_data: Collects data from Quantum ESPRESSO output files using a specified extractor function.
"""
from abc import ABC, abstractmethod
from typing import Tuple, Any, Callable

from core.input_handler import get_atomic_states
from ui.ui_helpers import print_error
from utils.file_parser import extract_atomic_states_info, extract_wannier_parameters


def collect_dft_data(path: str,
                     compound_name: str,
                     flag: str,
                     extractor_func: Callable,
                     *,
                     atom: str = None,
                     orbital: str = None,
                     is_pdos: bool = False) -> None | Tuple[None, bool] | Tuple[Any, bool]:
    """
    Collect data from Quantum ESPRESSO output files using a specified extractor function.

    Args:
        path (dict): The file path.
        compound_name (str): Name of the compound being analyzed.
        flag (str): Suffix for the file name (e.g., "_soc" or "").
        extractor_func (Callable): Function used to extract specific data from the file.
        atom (str): Atomic symbol
        orbital (str): Orbital type (e.g., "s", "p", "d")
        is_pdos (bool): Whether the data is from a PDOS file.

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
                data = extractor_func(path, compound_name, flag) if \
                    not is_pdos else extractor_func(path, compound_name, flag, is_pdos)
                return data, True

            case (True, False) | (False, True):
                raise ValueError(
                    """Both atom and orbital should be either None or not None.
                    If you want to extract atomic states, please provide both atom and orbital."""
                )

            case (False, False):
                data = extractor_func(path, compound_name, flag, atom, orbital) if \
                    not is_pdos else extractor_func(path, compound_name, flag, atom, orbital, is_pdos)
                return data, True

    except (FileNotFoundError, ValueError) as e:
        print_error(f"Error: {e}")
        return None, False

    return None, False

class DataExtractor(ABC):
    """
    Abstract base class for data extraction strategies.

    This class defines the interface for data extraction strategies, ensuring that
    all derived classes implement methods for extracting data, accessing paths, and
    providing success messages.
    """

    @abstractmethod
    def extract_data(self, path: str, compound_name: str, flag: str, **kwargs) -> Tuple[Any, bool]:
        """
        Extract data from a file.

        Args:
            path (str): Path to the file.
            compound_name (str): Name of the compound being analyzed.
            flag (str): Flag indicating spin-orbit coupling case (e.g., "_soc").
            **kwargs: Additional parameters for data extraction.

        Returns:
            Tuple[Any, bool]: Extracted data and a success flag.
        """
        pass

    @abstractmethod
    def get_path_key(self) -> str:
        """
        Get the key for accessing paths in the paths dictionary.

        Returns:
            str: Key for accessing paths.
        """
        pass

    @abstractmethod
    def get_success_message(self, **kwargs) -> str:
        """
        Get the success message for logging.

        Args:
            **kwargs: Additional parameters for generating the success message.

        Returns:
            str: Success message.
        """
        pass


class SimpleDataExtractor(DataExtractor):
    """
    Extractor for single value extraction.

    This class handles the extraction of single values from files using a specified
    extraction function.
    """

    def __init__(self, extractor_func: Callable, path_key: str, data_name: str):
        """
        Initialize the SimpleDataExtractor.

        Args:
            extractor_func (Callable): Function used to extract data from files.
            path_key (str): Key for accessing paths in the paths dictionary.
            data_name (str): Name of the data being extracted (e.g., "band numbers").
        """
        self.extractor_func = extractor_func
        self.path_key = path_key
        self.data_name = data_name

    def extract_data(self, path: str, compound_name: str, flag: str, **kwargs) -> Tuple[Any, bool]:
        """
        Extract data from a file.

        Args:
            path (str): Path to the file.
            compound_name (str): Name of the compound being analyzed.
            flag (str): Flag indicating spin-orbit coupling case (e.g., "_soc").
            **kwargs: Additional parameters for data extraction.

        Returns:
            Tuple[Any, bool]: Extracted data and a success flag.
        """
        is_pdos = kwargs.get('is_pdos', False)
        return collect_dft_data(path, compound_name, flag, self.extractor_func, is_pdos=is_pdos)

    def get_path_key(self) -> str:
        """
        Get the key for accessing paths in the paths dictionary.

        Returns:
            str: Key for accessing paths.
        """
        return self.path_key

    def get_success_message(self, **kwargs) -> str:
        """
        Get the success message for logging.

        Args:
            **kwargs: Additional parameters for generating the success message.

        Returns:
            str: Success message.
        """
        return f"Successfully extracted {self.data_name}.\n"


class AtomicStatesExtractor(DataExtractor):
    """
    Extractor for atomic states information.

    This class handles the extraction of atomic states information from files,
    including orbital weights and indices.
    """

    def __init__(self, path_key: str):
        """
        Initialize the AtomicStatesExtractor.

        Args:
            path_key (str): Key for accessing paths in the paths dictionary.
        """
        self.path_key = path_key
        self.atomic_projection_list = get_atomic_states()

    def extract_data(self, path: str, compound_name: str, flag: str, **kwargs) -> Tuple[Any, bool]:
        """
        Extract atomic states information from a file.

        Args:
            path (str): Path to the file.
            compound_name (str): Name of the compound being analyzed.
            flag (str): Flag indicating spin-orbit coupling case (e.g., "_soc").
            **kwargs: Additional parameters for data extraction.

        Returns:
            Tuple[Any, bool]: Extracted atomic states information and a success flag.
        """
        atomic_states_info = {}
        is_pdos = kwargs.get('is_pdos', False)

        for atom, orbital in self.atomic_projection_list:
            data, success = collect_dft_data(
                path, compound_name, flag, extract_atomic_states_info,
                atom=atom, orbital=orbital, is_pdos=is_pdos
            )

            if not success:
                return None, False

            atomic_states_info.update(data)

        return atomic_states_info, True

    def get_path_key(self) -> str:
        """
        Get the key for accessing paths in the paths dictionary.

        Returns:
            str: Key for accessing paths.
        """
        return self.path_key

    def get_success_message(self, **kwargs) -> str:
        """
        Get the success message for logging.

        Args:
            **kwargs: Additional parameters for generating the success message.

        Returns:
            str: Success message.
        """
        return "\nSuccessfully extracted atomic states information.\n"


class WannierDataExtractor(DataExtractor):
    """
    Extractor for Wannier parameters (alat and Fermi energy).

    This class handles the extraction of Wannier parameters from NSCF output files.
    """

    def __init__(self, path_key: str = "nscf_wannier_output_paths"):
        """
        Initialize the WannierDataExtractor.

        Args:
            path_key (str): Key for accessing paths in the paths dictionary. Defaults to "nscf_wannier_output_paths".
        """
        self.path_key = path_key

    def extract_data(self, path: str, compound_name: str, flag: str, **kwargs) -> Tuple[Any, bool]:
        """
        Extract Wannier parameters from NSCF output files.

        Args:
            path (str): Path to the file.
            compound_name (str): Name of the compound being analyzed.
            flag (str): Flag indicating spin-orbit coupling case (e.g., "_soc").
            **kwargs: Additional parameters for data extraction.

        Returns:
            Tuple[Any, bool]: Extracted Wannier parameters (alat and Fermi energy) and a success flag.
        """
        try:
            alat, fermi_energy = extract_wannier_parameters(path, compound_name, flag)
            return (alat, fermi_energy), True
        except (FileNotFoundError, ValueError) as e:
            print_error(f"Error extracting Wannier parameters: {e}")
            return None, False

    def get_path_key(self) -> str:
        """
        Get the key for accessing paths in the paths dictionary.

        Returns:
            str: Key for accessing paths.
        """
        return self.path_key

    def get_success_message(self, **kwargs) -> str:
        """
        Get the success message for logging.

        Args:
            **kwargs: Additional parameters for generating the success message.

        Returns:
            str: Success message.
        """
        return "Successfully extracted Wannier parameters.\n"