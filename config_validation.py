from typing import Dict, Any

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

def validate_directory_structure(directory_structure: Dict[str, str]) -> None:
    """Validate directory structure configuration."""
    required_dirs = {
        "scf",
        "scf_soc",
        "projected_bands",
        "projected_bands_soc",
    }

    if missing := required_dirs - set(directory_structure.keys()):
        raise ConfigValidationError(f"Missing required directory entries: {missing}")

    if not all(isinstance(path, str) for path in directory_structure.values()):
        raise ConfigValidationError("All directory paths must be strings")

def validate_file_patterns(patterns: Dict[str, Dict[str, str]]) -> None:
    """Validate file pattern configuration."""
    required_patterns = {
        "input": {
            "vc_relax_input",
            "scf_input",
            "pw_bands_input",
            "kpdos_input",
            "bands_input",
        },
        "output": {
            "vc_relax_output",
            "scf_output",
            "pw_bands_output",
            "kpdos_output",
            "projbands_output",
            "bands_gnu"
        }
    }

    for pattern_type in ("input", "output"):
        if pattern_type not in patterns:
            raise ConfigValidationError(f"Missing {pattern_type} patterns section")

        if missing := required_patterns[pattern_type] - set(patterns[pattern_type].keys()):
            raise ConfigValidationError(f"Missing required {pattern_type} patterns: {missing}")

        # Validate pattern format
        for pattern_name, pattern in patterns[pattern_type].items():
            if not isinstance(pattern, str):
                raise ConfigValidationError(f"Pattern {pattern_name} must be a string")
            if "{compound_name}" not in pattern:
                raise ConfigValidationError(f"Pattern {pattern_name} must contain {{compound_name}} placeholder")

def validate_config_structure(config: Dict[str, Any]) -> None:
    """Validate overall configuration structure."""
    required_sections = {"directory_structure", "file_patterns"}

    if missing := required_sections - set(config.keys()):
        raise ConfigValidationError(f"Missing required configuration sections: {missing}")

    validate_directory_structure(config["directory_structure"])
    validate_file_patterns(config["file_patterns"])