from path_gen_test import *
from data_extractor import *
from input_handler import get_atomic_states

def prepare_dft_info(config):
    # Determine which spin_orbit_flag to use
    if config["include_stress"]:
        # For strain analysis, we need one flag for each strain amount plus the base case
        spin_orbit_flag = ["" for _ in range(len(config["stress_amounts"]) + 1)] if config["stress_amounts"] else [""]
    else:
        spin_orbit_flag = ["", "_soc"]

    # Extracting band numbers
    number_of_bands_list = collect_band_numbers(
        config["paths"],
        config["compound_name"],
        spin_orbit_flag,
        config["paths"]["skip_soc"]
    )

    # Extracting Fermi energies
    fermi_energy_list = collect_fermi_energies(
        config["paths"],
        config["compound_name"],
        spin_orbit_flag,
        config["paths"]["skip_soc"]
    )

    number_of_atomic_states_list = collect_number_of_atomic_states(
        config["paths"],
        config["compound_name"],
        spin_orbit_flag,
        config["paths"]["skip_soc"]
    )

    atomic_states_info_list = collect_atomic_states_info(
        config["paths"],
        config["compound_name"],
        spin_orbit_flag,
        config["paths"]["skip_soc"]
    )

    # Updating configuration
    config["number_of_bands_list"] = number_of_bands_list
    config["fermi_energy_list"] = fermi_energy_list
    config["number_of_atomic_states_list"] = number_of_atomic_states_list
    config["atomic_states_info_list"] = atomic_states_info_list

    return config

if __name__ == "__main__":
    config = prepare_paths()
    config = prepare_dft_info(config)
    print("DFT information prepared successfully.")
    print(f"Number of bands list: {config['number_of_bands_list']}")
    print(f"Fermi energy list: {config['fermi_energy_list']}")
    print(f"Number of atomic states list: {config['number_of_atomic_states_list']}")
    print(f"Atomic states info list: {config['atomic_states_info_list']}")


