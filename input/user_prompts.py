"""User prompts for input generation in calculations.

This module provides functions to prompt the user for input values required
for various calculations, such as the number of bands and K-point mesh density.
It includes validation to ensure the inputs are correctly formatted and meet
the required constraints.

Functions:
    prompt_nbands(calculation_type: str, relativistic: bool = False) -> int:
        Prompts the user to input the number of bands for a given calculation type.
        Validates that the input is a positive integer.

    prompt_kmesh(calculation_type: str, relativistic: bool = False) -> tuple[int, int, int]:
        Prompts the user to input the K-point mesh density for a given calculation type.
        Validates that the input consists of three positive integers.
"""
from input.generators.exceptions import InputGenerationError
from ui.ui_helpers import prompt_input


def prompt_nbands(calculation_type: str, relativistic: bool = False) -> int:
    """
    Prompt the user to input the number of bands for a given calculation type.

    Args:
        calculation_type (str): The type of calculation (e.g., "bands", "dos").
        relativistic (bool): Whether the calculation is relativistic (SOC). Defaults to False.

    Returns:
        int: The number of bands entered by the user.

    Raises:
        ValueError: If the input is not a positive integer.
    """
    while True:
        try:
            number_of_bands = int(
                prompt_input(
                    f"Enter the number of bands for {calculation_type + ('_soc' if relativistic else '')}: ")
            )
            if number_of_bands <= 0:
                raise ValueError("Number of bands must be a positive integer.")
            return number_of_bands
        except ValueError:
            raise


def prompt_kmesh(calculation_type: str, relativistic: bool = False) -> tuple[int, int, int]:
    """
    Prompt the user to input the K-point mesh density for a given calculation type.

    Args:
        calculation_type (str): The type of calculation (e.g., "bands", "dos").
        relativistic (bool): Whether the calculation is relativistic (SOC). Defaults to False.

    Returns:
        tuple[int, int, int]: A tuple of three integers representing the K-point mesh density.

    Raises:
        ValueError: If the input is not three positive integers.
        TypeError: If the calculation type is not "bands" and the input is None.
        InputGenerationError: If the K-point mesh density is invalid for the given calculation type.
    """
    while True:
        try:
            kmesh_input = prompt_input(
                f"Enter K-point mesh density (e.g., '12 12 1') for {calculation_type + ('_soc' if relativistic else '')}: "
            )

            kmesh = tuple(map(int, kmesh_input.split()))
            if len(kmesh) != 3 or any(x <= 0 for x in kmesh):
                raise ValueError("K-point mesh density must be three positive integers.")
            return kmesh

        except ValueError:
            raise

        except TypeError:
            if calculation_type != "bands":
                raise InputGenerationError(f"K-point mesh density cannot be None for {calculation_type} calculation.")
