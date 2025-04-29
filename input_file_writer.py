"""Script to write input files for the project."""

from input_file_generator import *


project = initialize_project(argv, is_input=True)
skip_soc = project.skip_soc
write_input_files(project, skip_soc)