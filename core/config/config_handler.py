"""Configuration management for the project.

This module handles loading and validating the different configurations.
"""
import os

from core.config.plot_config import BandsPlotConfig, DOSPlotConfig
from core.config.project_config import ProjectConfig
from ui.ui_helpers import print_error, print_info, print_success, print_warning
from utils.config_validation import ConfigValidationError


def load_project_config(config_file: str = None,
                        config_type: str = "default") -> ProjectConfig:
    """
    Load and validate the project configuration.

    Args:
        config_file (str): Path to the JSON configuration file. Defaults to None.
        config_type (str): Type of configuration to load. Defaults to 'default'

    Returns:
        ProjectConfig: An instance of ProjectConfig with the loaded or default configuration.

    Raises:
        ConfigValidationError: If the configuration structure is invalid.
    """
    if config_type not in ("default", "bands", "pdos", "wannier"):
        raise ValueError("Invalid config_type. Must be 'default', 'bands', 'pdos', or 'wannier'.")

    try:
        if not config_file:
            print_info("Project configuration file not explicitly set. Finding an existing one...")
            user_id = os.getenv("COFFEE")
            if user_id:
                script_root_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "../.."))  # The root directory of the program
                config_file = os.path.join(script_root_dir, "..", user_id, "project_config.json")
                print_info(f"Config file path: {os.path.abspath(config_file)}")
                if os.path.exists(os.path.abspath(config_file)):
                    print_success(f"Config found for {user_id}")
                else:
                    print_warning(f"Config not found for {user_id}")
                    print_info("Using default configuration instead.")
                    config_file = "project_config.json"
            else:
                print_warning("Environment variable 'COFFEE' not set. Using default configuration.")
                config_file = "project_config.json"
        else:
            print_info(f"Loaded project configuration file: {os.path.abspath(config_file)}")

        return ProjectConfig.from_json(config_file, config_type)

    except ValueError as e:
        raise ConfigValidationError(f"Error in loading config file: {str(e)}")

    except ConfigValidationError as e:
        print_error(f"Configuration validation error: {str(e)}")
        print_info("Using default configuration instead.")

        return ProjectConfig.get_default_config(config_type)


def load_plot_config(config_file: str = None,
                     config_type: str = "bands") -> BandsPlotConfig | DOSPlotConfig:
    """
    Load and validate the plot configuration.

    Args:
        config_file (str): Path to the JSON configuration file. Defaults to None.
        config_type (str): Type of configuration to load. Defaults to 'bands'.

    Returns:
        BandsPlotConfig | DOSPlotConfig: An instance of BandsPlotConfig or DOSPlotConfig with the loaded or default configuration.
    """
    if config_type not in ("bands", "pdos"):
        raise ValueError("Invalid config_type. Must be 'bands' or 'pdos'.")

    try:
        if not config_file:
            print_info("Plot configuration file not explicitly set. Finding an existing one...")
            user_id = os.getenv("COFFEE")
            if user_id:
                script_root_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "../.."))  # The root directory of the program
                config_file = os.path.join(script_root_dir, "..", user_id, "plot_config.yaml")
                print_info(f"Config file path: {os.path.abspath(config_file)}")
                if os.path.exists(os.path.abspath(config_file)):
                    print_success(f"Config found for {user_id}")
                else:
                    print_warning(f"Config not found for {user_id}")
                    print_info("Using default configuration instead.")
                    config_file = "plot_config.yaml"
            else:
                print_warning("Environment variable 'COFFEE' not set. Using default configuration.")
                config_file = "plot_config.yaml"
        else:
            print_info(f"Loaded project configuration file: {os.path.abspath(config_file)}")

        return BandsPlotConfig.from_yaml(config_file) if config_type == "bands" else DOSPlotConfig.from_yaml(config_file)

    except ValueError as e:
        raise ConfigValidationError(f"Error in loading config file: {str(e)}")

    except ConfigValidationError as e:
        print_error(f"Configuration validation error: {str(e)}")
        print_info("Using default configuration instead.")

        return BandsPlotConfig.get_default_config() if config_type == "bands" else DOSPlotConfig.get_default_config()