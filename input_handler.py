"""Functions for handling user input.

This module provides utility functions to interact with the user for input
related to plotting projected bands. It includes functions to select the type
of bands to plot, input strain amounts, and specify atomic states for projection.
"""


def get_pbands_type():
    """
    Prompt the user to select the type of projected bands to plot.

    This function repeatedly asks the user whether they want to plot strained
    projected bands or normal projected bands until a valid input is provided.

    Returns:
        bool: True if the user chooses to plot strained projected bands, False otherwise.
    """
    while True:
        include_stress_input = input(
            'Do you want to plot strained projected bands instead? Type "yes" to plot strained projected bands and "no" to plot normal projected bands. '
        ).lower()

        if include_stress_input in ["yes", "no"]:
            return include_stress_input == "yes"
        else:
            print("Invalid input!")


def get_strain_amounts():
    """
    Prompt the user to input strain amounts for DFT calculations.

    This function repeatedly asks the user to provide a space-separated list of strain amounts
    in the format `1_<percent-of-stretch>`. It validates the input to ensure that at least one
    valid strain amount is provided and returns the list of strain amounts.

    Returns:
        list: A list of strings representing the strain amounts, e.g., ['1_10', '1_15', '1_20'].
    """

    while True:
        stress_amount_list_input = input("""Enter the strain amounts in units of relaxed coordinates in the form 1_<percent-of-stretch>.
For example 1_30 means the coordinates are stretched by 30%. Provide a space separated list of DFT calculations with the specified stress amounts
(e.g., 1_10 1_15 1_20):
""")

        # Cleaning up user input and error handling
        stress_amount_list = [
            amount for amount in stress_amount_list_input.split() if amount.strip()
        ]

        # List should not be empty
        if not stress_amount_list:
            print("Error: No valid strain amounts provided.")
        else:
            return stress_amount_list


def get_atomic_states():
    """
    Prepares and retrieves the atomic projection list for plotting projected bands.

    This function prompts the user to input atomic projections in the format
    <element name>-<orbital>, separated by spaces. It validates the input to ensure
    correctness and returns a list of atomic projections.

    Returns:
        list: A list of tuples where each tuple contains an element name (str) and
              an orbital type (str), e.g., [('O', 's'), ('C', 'p'), ('Fe', 'd')].
    """
    print("Preparing the atomic projection list for plotting projected bands...")

    supported_orbitals = ('s', 'p', 'd', 'pz', 'px', 'py', 'dz2', 'dxz', 'dyz', 'dx2y2', 'dxy')

    print(f"""
The supported orbitals are:
{', '.join(supported_orbitals)}
The projection list should be in pairs of <element name>-<orbital> separated by a single space.
Example usage: O-s C-p Fe-d
    """)

    # Loop to repeatedly prompt the user until valid input is provided
    while True:
        user_input = input("Enter the desired atomic orbitals you wish to project onto: ").strip()

        if not user_input:
            print("Input cannot be empty!")
            continue

        # Processing the user input and extracting atomic projection information
        atomic_projection_list = []
        for atomic_projection in user_input.split():

            # Validating the input format (must be in the form <element name>-<orbital>)
            if '-' not in atomic_projection:
                print("Invalid input format. Expected <element name>-<orbital>.")
                break

            element, orbital = atomic_projection.split('-')

            # Validating the element and orbital symbols
            if not element.isalpha():
                print("Invalid element symbol!")
                break

            if orbital not in supported_orbitals:
                print(f"Invalid orbital type! Supported types are: {', '.join(supported_orbitals)}")
                break

            atomic_projection_list.append((element, orbital))
        else:
            return atomic_projection_list
