from input.generators.sections import InputGenerationError
from ui.ui_helpers import prompt_input


def prompt_nbands(calculation_type: str, relativistic: bool = False) -> int:
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
