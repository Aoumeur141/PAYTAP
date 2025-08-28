

"""
pytap : Python Toolkit for Algerian Production suite

Copyright (c) 2025, Météo Algérie
------------------------------------------------------------------

``pytap`` is a package of classes and functions, designed to handle daily tasks
related to meteorological data processing and analysis, developed by Météo-Algérie.

It provides utilities for:
- Data fetching and configuration.
- General utility functions.
- Specific data manipulation and processing (e.g., GRIB files).
- Email communication.
- Logging and system interactions.
- Numerical operations (NumPy).
- Date and time handling.
- File system operations.
- 

********************************************************************************
"""

# --- Package Metadata ---
__version__ = "1.0.0"
__license__ = 'CeCILL-C'


# --- Custom Package Exception ---
class PyTapError(Exception):
    """Base exception class for the pytap package."""
    pass

from . import data_utils
from . import email_utils
from . import fetchdata
from . import grib_processor
from . import logging_utils
from . import numpy_utils
from . import system_utils
from . import date_time_utils
from . import file_operations
from . import config_utils


__version__ = "0.1.0"
__all__ = [
    "data_utils",
    "email_utils",
    "fetchdata",
    "grib_processor",
    "logging_utils",
    "numpy_utils",
    "system_utils",
    "date_time_utils",
    "file_operations",
    "config_utils",
]
