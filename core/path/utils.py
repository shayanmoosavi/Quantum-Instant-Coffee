import os
from typing import Dict


def get_project_directory(compound_name: str) -> str:
    """
    Get the project directory for the given compound.

    Args:
        compound_name (str): Name of the compound.

    Returns:
        str: The absolute path to the project directory.
    """
    script_root_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../.."))  # The root directory of the program
    user_id = os.getenv("COFFEE")
    user_path = os.path.join(script_root_dir, "..", user_id) if user_id else ".."
    root_dir = os.path.abspath(user_path)  # The root directory of the project
    return os.path.join(root_dir, compound_name)  # The calculation directory


def has_soc_directories(directory_structure: Dict[str, str]) -> bool:
    """
    Check if the configuration contains SOC-related directories.

    Args:
        directory_structure (Dict[str, str]): A dictionary where keys are directory names
            and values are their corresponding paths.

    Returns:
        bool: True if SOC directories are present, False otherwise.
    """
    soc_dirs = {
        "scf_soc",
        "projected_bands_soc",
        "pdos_soc",
        "pseudo_rel"
    }

    return bool(soc_dirs & set(directory_structure.keys()))
