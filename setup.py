# PyTAP-main/setup.py

from setuptools import setup, find_packages
import os # Added for os.path.exists

setup(
    name='pytap',
    version='1.0.0', 
    author_email='your.email@example.com',
    description='Python Toolkit for Automated Processes (PyTAP)',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    packages=find_packages(where='src'), # Tells setuptools to look for packages in the 'src' directory
    package_dir={'': 'src'}, # Maps the root package to the 'src' directory
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha', # Indicate development stage
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    keywords=['automation', 'utility', 'toolkit', 'data-processing', 'ftp', 'file-operations', 'system-commands', 'logging', 'time-utilities'], # Added keywords
    python_requires='>=3.6', # Minimum Python version required
    install_requires=[
        # List any external libraries your package depends on here.
        # For now, ftplib, logging, os, fnmatch, shutil, datetime, subprocess are built-in.
        # If you add new features that need external libraries (e.g., requests, pandas), list them here.
    ],
)
