# ~/Téléchargements/PyTAP-main/setup.py

from setuptools import setup, find_packages
import os # Import os to check for README.md

setup(
    name='pytaps',
    version='0.1.0', # Or whatever your current version is
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    # --- ADD OR UPDATE THIS SECTION ---
    install_requires=[
        # Add any existing dependencies here, e.g., 'paramiko' if you used it for SFTP
        # 'ftplib' is built-in, so no need to list it here
        'epygram',  # NEW: For GRIB file processing
        'numpy',    # NEW: For numerical operations
        'pandas',   # NEW: For data manipulation (DataFrames)
    ],

    python_requires='>=3.6', # Or your specific Python version like '>=3.10'
)
