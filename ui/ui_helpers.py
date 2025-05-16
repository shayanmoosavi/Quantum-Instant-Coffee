from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.progress import track

# Custom color theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "green",
    "header": "bold purple",
    "prompt": "bold bright_blue",
    "highlight": "bold magenta"
})

console = Console(theme=custom_theme)


def print_info(message: str, highlight: bool = True):
    console.print(f"[info]{message}[/info]", highlight=highlight)


def print_warning(message: str):
    console.print(f"[warning]{message}[/warning]")


def print_error(message: str):
    console.print(f"[error]{message}[/error]")


def print_success(message: str):
    console.print(f"[success]{message}[/success]")


def print_header(message: str, width=None):
    console.print(Panel(message, box.HORIZONTALS, style="header", width=width))


def print_list(title: str, items: list[str]):
    table = Table(title=title, box=box.ROUNDED, width=40)
    table.add_column("Index", style="highlight", justify="right")
    table.add_column("Filename", style="info", justify="left")
    for i, item in enumerate(items, 1):
        table.add_row(str(i), item)
    console.print(table)


def prompt_input(message: str) -> str:
    return console.input(f"[prompt]{message}[/prompt] ")


# Simple iterable progress
def progress_track(iterable, description="Processing"):
    return track(iterable, description=f"[cyan]{description}[/cyan]")


if __name__ == "__main__":
    # Example usage
    print_header("Welcome to Quantum Instant Coffee")
    print_info("This is an informational message.")
    print_warning("This is a warning message.")
    print_error("This is an error message.")
    print_success("This is a success message.")

    items = ["item1.txt", "item2.txt", "item3.txt"]
    print_list("Available Files", items)

    user_input = prompt_input("Please enter your choice: ")
    print_success(f"You selected: {user_input}")