"""Configuration management for the project.

This module handles loading and validating the different configurations.
"""
import os
from abc import ABC, abstractmethod

from core.config import BandsPlotConfig, DOSPlotConfig, ProjectConfig
from ui.display import RichDisplay
from utils.config_validation import ConfigValidationError


class BaseConfigLoader(ABC):
    """Abstract base class for configuration loaders."""

    def __init__(self, display_handler: RichDisplay):
        self.display_handler = display_handler

    @abstractmethod
    def get_config_filename(self, config_type: str) -> str:
        """Get the default config filename for the given type."""
        pass

    @abstractmethod
    def get_valid_config_types(self) -> tuple:
        """Get tuple of valid configuration types."""
        pass

    @abstractmethod
    def load_config_from_file(self, config_file: str,
                              config_type: str) -> ProjectConfig | BandsPlotConfig | DOSPlotConfig:
        """Load configuration from file using the appropriate config class method."""
        pass

    @abstractmethod
    def get_default_config(self, config_type: str) -> ProjectConfig | BandsPlotConfig | DOSPlotConfig:
        """Get default configuration using the appropriate config class method."""
        pass

    def _find_config_file(self, config_file: str, config_type: str) -> str:
        """
        Find the configuration file, checking user-specific locations if needed.

        Args:
            config_file: Explicitly provided config file path
            config_type: Type of configuration

        Returns:
            str: Path to the configuration file to use
        """
        if config_file:
            self.display_handler.display_info(f"Using explicitly provided config file: {os.path.abspath(config_file)}")
            return config_file

        self.display_handler.display_info("Configuration file not explicitly set. Finding an existing one...")

        user_id = os.getenv("COFFEE")
        if user_id:
            script_root_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../.."))
            default_filename = self.get_config_filename(config_type)
            config_file = os.path.join(script_root_dir, "..", user_id, default_filename)

            self.display_handler.display_info(f"Config file path: {os.path.abspath(config_file)}")

            if os.path.exists(os.path.abspath(config_file)):
                self.display_handler.display_success(f"Config found for {user_id}")
                return config_file
            else:
                self.display_handler.display_warning(f"Config not found for {user_id}")
                self.display_handler.display_info("Using default configuration instead.")
                return self.get_config_filename(config_type)
        else:
            self.display_handler.display_warning("Environment variable 'COFFEE' not set. Using default configuration.")
            return self.get_config_filename(config_type)

    def load_config(self, config_file: str = None,
                    config_type: str = None) -> ProjectConfig | BandsPlotConfig | DOSPlotConfig:
        """
        Load and validate configuration.

        Args:
            config_file: Path to the configuration file. Defaults to None.
            config_type: Type of configuration to load.

        Returns:
            Configuration instance with loaded or default configuration.

        Raises:
            ValueError: If config_type is invalid.
            ConfigValidationError: If configuration structure is invalid.
        """
        if config_type not in self.get_valid_config_types():
            valid_types = "', '".join(self.get_valid_config_types())
            raise ValueError(f"Invalid config_type. Must be one of: '{valid_types}'.")

        try:
            final_config_file = self._find_config_file(config_file, config_type)
            return self.load_config_from_file(final_config_file, config_type)

        except ValueError as e:
            raise ConfigValidationError(f"Error in loading config file: {str(e)}")

        except ConfigValidationError as e:
            self.display_handler.display_error(f"Configuration validation error: {str(e)}")
            self.display_handler.display_info("Using default configuration instead.")
            return self.get_default_config(config_type)


class ProjectConfigLoader(BaseConfigLoader):
    """Configuration loader for project configurations."""

    def get_config_filename(self, config_type: str) -> str:
        return "project_config.json"

    def get_valid_config_types(self) -> tuple:
        return "default", "bands", "pdos", "wannier"

    def load_config_from_file(self, config_file: str, config_type: str) -> ProjectConfig:
        return ProjectConfig.from_json(config_file, config_type)

    def get_default_config(self, config_type: str) -> ProjectConfig:
        return ProjectConfig.get_default_config(config_type)


class PlotConfigLoader(BaseConfigLoader):
    """Configuration loader for plot configurations."""

    def get_config_filename(self, config_type: str) -> str:
        return "plot_config.yaml"

    def get_valid_config_types(self) -> tuple:
        return "bands", "pdos"

    def load_config_from_file(self, config_file: str, config_type: str) -> BandsPlotConfig | DOSPlotConfig:
        if config_type == "bands":
            return BandsPlotConfig.from_yaml(config_file)
        else:
            return DOSPlotConfig.from_yaml(config_file)

    def get_default_config(self, config_type: str) -> BandsPlotConfig | DOSPlotConfig:
        if config_type == "bands":
            return BandsPlotConfig.get_default_config()
        else:
            return DOSPlotConfig.get_default_config()


def load_project_config(display_handler: RichDisplay,
                        config_file: str = None,
                        config_type: str = "default") -> ProjectConfig:
    """
    Load and validate the project configuration.

    Args:
        display_handler (RichDisplay): Display handler for UI output.
        config_file (str): Path to the JSON configuration file. Defaults to None.
        config_type (str): Type of configuration to load. Defaults to 'default'

    Returns:
        ProjectConfig: An instance of ProjectConfig with the loaded or default configuration.
        display_handler (RichDisplay): Display handler for UI output.

    Raises:
        ConfigValidationError: If the configuration structure is invalid.
    """
    loader = ProjectConfigLoader(display_handler)
    return loader.load_config(config_file, config_type)


def load_plot_config(display_handler: RichDisplay,
                     config_file: str = None,
                     config_type: str = "bands") -> BandsPlotConfig | DOSPlotConfig:
    """
    Load and validate the plot configuration.

    Args:
        display_handler (RichDisplay): Display handler for UI output.
        config_file (str): Path to the JSON configuration file. Defaults to None.
        config_type (str): Type of configuration to load. Defaults to 'bands'.

    Returns:
        BandsPlotConfig | DOSPlotConfig: An instance of BandsPlotConfig or DOSPlotConfig with the loaded or default configuration.
    """
    loader = PlotConfigLoader(display_handler)
    return loader.load_config(config_file, config_type)
