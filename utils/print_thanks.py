from time import sleep

from ui.ui_helpers import print_header, console


def print_animated_ascii(filepath: str, delay: float = 0.1) -> None:
    with open(filepath) as f:
        ascii_lines = f.readlines()
    print_header("Thank you")
    for line in ascii_lines:
        if line.strip():  # Only animate non-empty lines
            console.print(line.rstrip())
            sleep(delay)
        else:
            console.print(line.rstrip())  # Print empty lines immediately