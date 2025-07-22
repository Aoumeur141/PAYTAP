#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Expose functions from fetchdata module
from .fetchdata import create_ftp_client, fetch_files, list_remote_files

# Expose functions from utils module
# run_next_program has been removed from utils.py
from .utils import generate_met_filename, check_local_files_exist, move_files_by_pattern


class fireError(Exception):
    """Errors class for the package."""
    pass

# Removed redundant 'from . import module' imports.
# If 'config' module is genuinely used for package-wide configuration,
# you might want to expose specific config variables, but not the module itself
# unless there's a strong reason. For now, assuming it's not needed directly exposed.