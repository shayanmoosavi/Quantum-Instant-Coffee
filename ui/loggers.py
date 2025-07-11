""" Logging module for the UI.

This module defines an abstract base class `Logger` and the concrete implementations of the
Logger class for different use cases.

Classes:
    Logger: Abstract base class for loggers.
    RichLogger: Logger implementation using the Rich library for formatted output.

"""

from abc import ABC, abstractmethod

from ui_helpers import *


class Logger(ABC):
    """
    Abstract base class for loggers.

    This class defines the interface for logging messages. Subclasses must implement
    the following methods:
        - info: Log an informational message.
        - warning: Log a warning message.
        - error: Log an error message.
        - success: Log a success message.
    """

    @abstractmethod
    def info(self, message: str):
        """
        Log an informational message.

        Args:
            message (str): The message to log.
        """
        pass

    @abstractmethod
    def warning(self, message: str):
        """
        Log a warning message.

        Args:
            message (str): The message to log.
        """
        pass

    @abstractmethod
    def error(self, message: str):
        """
        Log an error message.

        Args:
            message (str): The message to log.
        """
        pass

    @abstractmethod
    def success(self, message: str):
        """
        Log a success message.

        Args:
            message (str): The message to log.
        """
        pass


class RichLogger(Logger):
    """
    Logger implementation using the Rich library for formatted output.

    This class provides concrete implementations of the `Logger` interface methods for rich
    formatted output in the console.
    """

    def info(self, message: str):
        """
        Log an informational message to the console.

        Args:
            message (str): The message to log.
        """
        print_info(message)

    def warning(self, message: str):
        """
        Log a warning message to the console.

        Args:
            message (str): The message to log.
        """
        print_warning(message)

    def error(self, message: str):
        """
        Log an error message to the console.

        Args:
            message (str): The message to log.
        """
        print_error(message)

    def success(self, message: str):
        """
        Log a success message to the console.

        Args:
            message (str): The message to log.
        """
        print_success(message)
