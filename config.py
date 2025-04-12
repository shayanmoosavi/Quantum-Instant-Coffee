"""Configuration management for the project."""
import json


def load_config(config_file="config.json"):
    """Load configuration from a JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_config()


def get_default_config():
    """Return default configuration settings."""
    return {
        "directory_structure": {
            "scf": "scf",
            "scf_soc": "spin_orbit/scf",
            "projected_bands": "projected_bands",
            "projected_bands_soc": "spin_orbit/projected_bands",
            "strain": "strain"
        },
        "file_patterns": {
            "bands_output": "{compound_name}_bands{flag}.pw.out",
            "kpdos_output": "{compound_name}{flag}.kpdos.out",
            "projbands_output": "{compound_name}{flag}.projbands",
            "bands_gnu": "{compound_name}.bands.gnu",
            "scf_output": "{compound_name}_scf{flag}.pw.out"
        }
    }