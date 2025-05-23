"""Configuration management for the project.

This module handles loading and validating the different configurations.
"""
import os

from core.plot_config import BandsPlotConfig, DOSPlotConfig
from core.project_config import ProjectConfig
from ui.ui_helpers import print_error, print_info, print_success, print_warning
from utils.config_validation import ConfigValidationError


def load_config(config_file: str = None,
                config_type: str = "project") -> ProjectConfig | BandsPlotConfig | DOSPlotConfig:
    """
    Load and validate the project configuration.

    Args:
        config_file (str): Path to the JSON configuration file. Defaults to None.
        config_type (str): Type of configuration to load. Defaults to 'project'

    Returns:
        ProjectConfig: An instance of ProjectConfig with the loaded or default configuration.

    Raises:
        ConfigValidationError: If the configuration structure is invalid.
    """
    if config_type not in ("project", "bands", "dos"):
        raise ValueError("Invalid config_type. Must be 'project', 'bands', or 'dos'.")

    is_project_config = config_type == "project"
    try:
        if not config_file:
            print_info("Loading project configuration file...") if is_project_config \
                else print_info("Plot configuration file not explicitly set. Finding an existing one...")
            user_id = os.getenv("COFFEE")
            if user_id:
                script_root_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), ".."))  # The root directory of the program
                config_file = os.path.join(script_root_dir, "..", user_id,
                                           "project_config.json" if is_project_config else "plot_config.yaml")
                print_info(f"Config file path: {os.path.abspath(config_file)}")
                if os.path.exists(os.path.abspath(config_file)):
                    print_success(f"Config found for {user_id}")
                else:
                    print_warning(f"Config not found for {user_id}")
                    print_info("Using default configuration instead.")
                    config_file = "project_config.json" if is_project_config else "plot_config.yaml"
            else:
                print_warning("Environment variable 'COFFEE' not set. Using default configuration.")
                config_file = "project_config.json" if is_project_config else "plot_config.yaml"
        else:
            print_info(f"Loaded project configuration file: {config_file}") if is_project_config \
                else print_info(f"Loaded plot configuration file: {os.path.abspath(config_file)}")
        match config_type:
            case "project":
                return ProjectConfig.from_json(config_file)
            case "bands":
                return BandsPlotConfig.from_yaml(config_file)
            case "dos":
                return DOSPlotConfig.from_yaml(config_file)
            case _:
                raise ValueError("Invalid config_type. Must be 'project', 'bands', or 'dos'.")

    except ValueError as e:
        raise ConfigValidationError(f"Error in loading config file: {str(e)}")

    except ConfigValidationError as e:
        print_error(f"Configuration validation error: {str(e)}")
        print_info("Using default configuration instead.")

        match config_type:
            case "project":
                return ProjectConfig.get_default_config()
            case "bands":
                return BandsPlotConfig.get_default_config()
            case "dos":
                return DOSPlotConfig.get_default_config()
            case _:
                raise ValueError("Invalid config_type. Must be 'project', 'bands', or 'dos'.")
