# src/pytaps/__init__.py

# This file marks the 'pytaps' directory as a Python package.

# Define the package version. This is good practice for all Python packages.
# It helps you and others know which version of your toolkit they are using.
__version__ = "0.1.0" # You can change this version number as your package grows

# Import common functions directly into the package's top level.
# This makes them easy to use, e.g., pytaps.merge_binary_files()
# We are importing from the *correct* files: file_operations and system_utils.

from .fetchdata import (
    create_ftp_client,
    list_remote_files,
    fetch_files
)

from .file_operations import (
    generate_met_filename,
    check_local_files_exist,
    move_files_by_pattern,
    merge_binary_files, # <-- New function
    delete_files        # <-- New function
)

from .system_utils import ( # <-- New module
    execute_command     # <-- New function
)
