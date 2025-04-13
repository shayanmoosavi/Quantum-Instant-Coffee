"""Functions for handling user input."""


def get_pbands_type():
    """Get the projected bands type (e.g. strained projected bands or normal projected bands) from user input."""
    while True:
        include_stress_input = input(
            'Do you want to plot strained projected bands instead? Type "yes" to plot strained projected bands and "no" to plot normal projected bands. '
        ).lower()

        if include_stress_input in ["yes", "no"]:
            return include_stress_input == "yes"
        else:
            print("Invalid input!")


def get_strain_amounts():
    """Get strain amounts from user input."""
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
        exit(1)

    return stress_amount_list
