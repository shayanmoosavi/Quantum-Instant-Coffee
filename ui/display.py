""" Module for displaying information in the UI.

"""
import os.path
from abc import ABC, abstractmethod
from typing import Iterable

from rich.table import Table
import rich.box

from ui.loggers import RichLogger
from ui.print_thanks import print_animated_ascii
from ui.ui_helpers import print_header, console, progress_track


class Display(ABC):
    """
    Abstract base class for displaying information in the UI.

    This class defines the interface for displaying various types of information.
    Subclasses must implement the following methods:
        - display_header: Display a section header with a title.
        - display_table: Display a table with given headers and data.
        - display_progress: Display a progress bar.
        - display_thanks: Display a 'thank you' message to the user at the end of execution.
        - display_info: Display an informational message.
        - display_warning: Display a warning message.
        - display_error: Display an error message.
        - display_success: Display a success message.
    """

    @abstractmethod
    def display_header(self, title: str):
        """
        Display a section header with a title.

        Args:
            title (str): The title of the section.
        """
        pass

    @abstractmethod
    def display_table(self, headers: list[str], data: list[list[str]], title: str = None):
        """
        Display a table with given headers and data.

        Args:
            headers (list[str]): List of column headers.
            data (list[list[str]]): List of rows, where each row is a list of strings.
            title (str): Optional title for the table.
        """
        pass

    @abstractmethod
    def display_progress(self, iterable: Iterable, description: str = "Processing"):
        """
        Display a progress bar.

        Args:
            iterable (Iterable): An iterable to track progress over.
            description (str): Description for the progress bar.
        """
        pass

    @abstractmethod
    def display_thanks(self):
        """
        Display a 'thank you' message to the user at the end of execution.
        """
        pass

    @abstractmethod
    def display_info(self, message: str):
        """
        Display an informational message.

        Args:
            message (str): The message to display.
        """
        pass

    @abstractmethod
    def display_warning(self, message: str):
        """
        Display a warning message.

        Args:
            message (str): The message to display.
        """
        pass

    @abstractmethod
    def display_error(self, message: str):
        """
        Display an error message.

        Args:
            message (str): The message to display.
        """
        pass

    @abstractmethod
    def display_success(self, message: str):
        """
        Display a success message.

        Args:
            message (str): The message to display.
        """
        pass


class RichDisplay(Display):
    """
    Concrete implementation of the Display class using the Rich library.

    This class provides rich formatted output for displaying headers, tables, and messages.

    """

    def __init__(self):
        self.logger = RichLogger()

    def display_header(self, title: str):
        """
        Display a section header with a title.

        Args:
            title (str): The title of the section.
        """
        print_header(title)

    def display_table(self, headers: list[str],
                      data: list[list[str]],
                      title: str = None,
                      column_styles: list[str] = None):
        """
        Display a table with given headers and data.

        Args:
            headers (list[str]): List of column headers.
            data (list[list[str]]): List of rows, where each row is a list of strings.
            title (str): Optional title for the table.
            column_styles (list[str]): Optional list of styles for each column header.
        """

        table = Table(title=title, box=rich.box.ROUNDED)

        if not column_styles:
            for header in headers:
                table.add_column(header, style="cyan")
        else:
            for header, style in zip(headers, column_styles):
                table.add_column(header, style=style)

        for row in data:
            table.add_row(*row)

        console.print(table)

    def display_progress(self, iterable: Iterable, description: str = "Processing"):
        """
        Display a progress bar.

        Args:
            iterable (Iterable): An iterable to track progress over.
            description (str): Description for the progress bar.
        """

        progress_track(iterable, description)

    def display_thanks(self):
        """
        Display a 'thank you' message to the user at the end of execution.

        """
        script_root_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")  # The root directory of the program
        )

        print_animated_ascii(os.path.join(script_root_dir, "ascii-art.txt"))

    def display_info(self, message: str):
        """
        Display an informational message.

        Args:
            message (str): The message to display.
        """
        self.logger.info(message)

    def display_warning(self, message: str):
        """
        Display a warning message.

        Args:
            message (str): The message to display.
        """
        self.logger.warning(message)

    def display_error(self, message: str):
        """
        Display an error message.

        Args:
            message (str): The message to display.
        """
        self.logger.error(message)

    def display_success(self, message: str):
        """
        Display a success message.

        Args:
            message (str): The message to display.
        """
        self.logger.success(message)
