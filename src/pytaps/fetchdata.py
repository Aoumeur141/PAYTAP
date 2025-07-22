# PyTAP_repository/src/pytaps/fetchdata.py

import os
from ftplib import FTP
import socket
import fnmatch # For pattern matching filenames
import logging # Added for logging

logger = logging.getLogger(__name__) # Get a logger for this module

def create_ftp_client(host, username, password, port=21): # Default FTP port is 21
    """Creates an FTP connection."""
    ftp = FTP()
    try:
        logger.info(f"Attempting to connect to FTP server {host}:{port}...")
        ftp.connect(host, port, timeout=30) # Add a timeout
        ftp.login(user=username, passwd=password)
        logger.info(f"Successfully connected and logged in to {host}.")
        return ftp
    except (socket.gaierror, ConnectionRefusedError, TimeoutError) as e:
        logger.error(f"Failed to connect to FTP server {host}. Error: {e}")
        raise ConnectionError(f"Failed to connect to FTP server {host}. Error: {e}")
    except Exception as e:
        logger.error(f"FTP login failed for {username} on {host}. Error: {e}")
        raise ConnectionError(f"FTP login failed for {username} on {host}. Error: {e}")


def list_remote_files(host, username, password, remote_dir, filename_pattern=None):
    """
    Lists files in a remote FTP directory, optionally filtering by pattern.

    Args:
        host (str): FTP server host.
        username (str): FTP username.
        password (str): FTP password.
        remote_dir (str): The remote directory to list.
        filename_pattern (str, optional): A glob-style pattern to filter files.
                                          If None, all files are returned.

    Returns:
        list: A list of filenames (str) matching the pattern, or all filenames if no pattern.
    Raises:
        ConnectionError: If connection or listing fails.
    """
    ftp = None
    matching_files = []
    try:
        logger.info(f"Listing files in remote directory: {remote_dir} on {host} (pattern: {filename_pattern or 'None'})...")
        ftp = create_ftp_client(host=host, username=username, password=password)
        ftp.set_pasv(True)
        ftp.cwd(remote_dir)

        all_remote_files = ftp.nlst() # nlst() returns a list of filenames
        logger.debug(f"Found {len(all_remote_files)} files in {remote_dir} before filtering.")

        if filename_pattern:
            for filename in all_remote_files:
                if fnmatch.fnmatch(filename, filename_pattern):
                    matching_files.append(filename)
            logger.info(f"Found {len(matching_files)} files matching pattern '{filename_pattern}'.")
        else:
            matching_files = all_remote_files # No pattern, return all
            logger.info(f"Returning all {len(matching_files)} files (no pattern specified).")

    except Exception as e:
        logger.error(f"Failed to list files on FTP server {host}/{remote_dir}. Error: {e}")
        raise ConnectionError(f"Failed to list files on FTP server {host}/{remote_dir}. Error: {e}")
    finally:
        if ftp:
            ftp.quit()
    return matching_files

def fetch_files(host, username, password, remote_base_dir, file_date_str, filename_pattern_template, local_base_dir):
    """Downloads files via FTP based on configuration parameters."""
    logger.info("Starting FTP file fetch process.")
    ftp = None # Initialize ftp to None
    try:
        ftp = create_ftp_client(host=host, username=username, password=password)
        ftp.set_pasv(True) # Set passive mode, usually better for firewalls

        # Change to the remote base directory
        try:
            ftp.cwd(remote_base_dir)
            logger.info(f"Changed remote directory to: {remote_base_dir}")
        except Exception as e:
            logger.error(f"Remote directory {remote_base_dir} not found or accessible: {e}")
            raise FileNotFoundError(f"Remote directory {remote_base_dir} not found or accessible: {e}")

        # Construct the full file pattern for the current date
        full_file_pattern = filename_pattern_template.format(date=file_date_str)
        logger.info(f"Looking for files matching pattern: '{full_file_pattern}'")

        # Create local directory if it doesn't exist
        os.makedirs(local_base_dir, exist_ok=True)
        logger.info(f"Local download directory: {local_base_dir}")

        # List files in the remote directory that match the pattern
        remote_files_to_download = []
        try:
            all_remote_files = ftp.nlst()
            for filename in all_remote_files:
                if fnmatch.fnmatch(filename, full_file_pattern):
                    remote_files_to_download.append(filename)
            logger.info(f"Found {len(remote_files_to_download)} files matching pattern on remote server.")

        except Exception as e:
            logger.error(f"Error listing files in {remote_base_dir}: {e}")
            raise

        if not remote_files_to_download:
            logger.warning(f"No files found matching pattern '{full_file_pattern}' in '{remote_base_dir}' to download.")
            return # Exit if no files to download

        for remote_filename in remote_files_to_download:
            local_file_path = os.path.join(local_base_dir, remote_filename)

            logger.info(f"Downloading {remote_filename} to {local_file_path}")
            with open(local_file_path, 'wb') as local_file:
                ftp.retrbinary(f"RETR {remote_filename}", local_file.write)
                logger.info(f"Successfully downloaded {remote_filename}")

    except Exception as e:
        logger.error(f"An error occurred during FTP transfer: {e}")
        raise # Re-raise to allow the calling script to catch it
    finally:
        if ftp:
            ftp.quit() # Close the FTP connection
    logger.info("FTP file fetch process completed.")

