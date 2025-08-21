# PyTAP_repository/src/pytaps/fetchdata.py
import os
from ftplib import FTP
import socket
import fnmatch
import logging
import paramiko
from pathlib import Path
from typing import List, Dict, Union, Optional, Tuple # Added Tuple for client return type

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

def create_sftp_client(host: str, username: str, password: str, port: int = 22, logger_instance: Optional[logging.Logger] = None) -> Tuple[paramiko.SSHClient, paramiko.SFTPClient]:
    """Internal helper: Establishes an SFTP connection using paramiko.
    Returns both the SSHClient and SFTPClient for proper closing."""
    current_logger = logger_instance if logger_instance is not None else logger
    current_logger.info(f"Attempting to create SFTP client for {host}:{port} with user {username}.")
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(host, port, username, password)
        sftp_client = ssh_client.open_sftp()
        current_logger.info(f"Successfully connected to SFTP server: {host}")
        return ssh_client, sftp_client
    except Exception as e:
        current_logger.error(f"Failed to connect to SFTP server {host}. Error: {e}")
        # Ensure SSH client is closed if SFTP client opening fails
        if ssh_client:
            ssh_client.close()
        raise ConnectionError(f"Failed to connect to SFTP server {host}. Error: {e}")
    
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



def create_remote_client(
    protocol: str,
    host: str,
    username: str,
    password: str,
    port: Optional[int] = None, # Port now optional, defaults based on protocol
    logger_instance: Optional[logging.Logger] = None
) -> Union[FTP, paramiko.SFTPClient, Tuple[paramiko.SSHClient, paramiko.SFTPClient]]:
    """
    Creates and returns a remote file transfer client (FTP or SFTP) based on the protocol.

    Args:
        protocol (str): The transfer protocol to use ('ftp' or 'sftp').
        host (str): The remote server host.
        username (str): The username for authentication.
        password (str): The password for authentication.
        port (Optional[int]): The port for the connection. If None, defaults to 21 for FTP, 22 for SFTP.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.

    Returns:
        Union[FTP, paramiko.SFTPClient, Tuple[paramiko.SSHClient, paramiko.SFTPClient]]:
            An active FTP client (FTP object) for 'ftp' protocol.
            For 'sftp' protocol, returns a tuple of (paramiko.SSHClient, paramiko.SFTPClient)
            because the SSHClient needs to be closed to properly close the SFTPClient.

    Raises:
        ValueError: If an unsupported protocol is specified.
        ConnectionError: If connection to the remote server fails.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    
    if protocol.lower() == 'ftp':
        actual_port = port if port is not None else 21
        # CORRECTED LINE: Removed 'current_logger' from arguments for create_ftp_client
        return create_ftp_client(host, username, password, actual_port) 
    elif protocol.lower() == 'sftp':
        actual_port = port if port is not None else 22
        # For SFTP, we return both the SSHClient and SFTPClient
        # so the caller can manage closing the SSHClient.
        return create_sftp_client(host, username, password, actual_port, current_logger)
    else:
        current_logger.error(f"Unsupported protocol specified: {protocol}. Must be 'ftp' or 'sftp'.")
        raise ValueError(f"Unsupported protocol: {protocol}")


def fetch_remote_files(
    protocol: str,
    host: str,
    port: Optional[int], # Port can be Optional now
    username: str,
    password: str,
    files_to_process: List[Dict[str, Union[str, Path]]],
    logger_instance: Optional[logging.Logger] = None
) -> None:
    """
    Downloads files from a remote server via FTP or SFTP, handling local existence and size checks.

    Args:
        protocol (str): The transfer protocol to use ('ftp' or 'sftp').
        host (str): The remote server host.
        port (Optional[int]): The port for the connection. If None, defaults based on protocol.
        username (str): The username for authentication.
        password (str): The password for authentication.
        files_to_process (List[Dict[str, Union[str, Path]]]): A list of dictionaries,
                                                                each containing 'remote_path'
                                                                and 'local_path' for files to handle.
            The 'local_path' should be a Path object or convertible to one.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.

    Raises:
        ValueError: If an unsupported protocol is specified.
        ConnectionError: If connection to the remote server fails.
        Exception: For other errors during file transfer.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    current_logger.info(f"Starting {protocol.upper()} file fetching process for {len(files_to_process)} files.")

    client = None
    ssh_client = None # Only used for SFTP to ensure SSHClient is closed

    try:
        # Use the new unified client creation function
        client_or_tuple = create_remote_client(protocol, host, username, password, port, current_logger)

        if protocol.lower() == 'sftp':
            ssh_client, client = client_or_tuple # Unpack the tuple for SFTP
        else: # FTP
            client = client_or_tuple

        for file_info in files_to_process:
            remote_file_path = file_info['remote_path']
            local_file_path = Path(file_info['local_path'])
            
            local_file_path.parent.mkdir(parents=True, exist_ok=True)

            remote_size = -1
            download_needed = True

            if local_file_path.exists():
                local_size = local_file_path.stat().st_size
                if protocol.lower() == 'sftp':
                    try:
                        remote_stat = client.stat(remote_file_path)
                        remote_size = remote_stat.st_size
                        if local_size == remote_size:
                            current_logger.info(f"Local file {local_file_path.name} already exists and sizes match ({local_size} bytes). Skipping download.")
                            download_needed = False
                        else:
                            current_logger.info(f"Local file {local_file_path.name} exists but sizes differ (local={local_size}, remote={remote_size}). Re-downloading.")
                    except FileNotFoundError:
                        current_logger.warning(f"Remote SFTP file not found: {remote_file_path}. Cannot verify size or download.")
                        download_needed = False
                    except Exception as stat_e:
                        current_logger.error(f"Could not get remote SFTP file stats for {remote_file_path}: {stat_e}. Attempting download anyway (size unknown).")
                elif protocol.lower() == 'ftp':
                    try:
                        # FTP.size() generally requires changing directory or providing full path
                        # Let's try to get the size in the remote_file_path's directory
                        original_cwd = client.pwd() # Store current working directory
                        client.cwd(os.path.dirname(remote_file_path))
                        remote_size = client.size(os.path.basename(remote_file_path))
                        client.cwd(original_cwd) # Go back to original directory
                        
                        if remote_size is not None and local_size == remote_size:
                            current_logger.info(f"Local file {local_file_path.name} already exists and sizes match (FTP size check). Skipping download.")
                            download_needed = False
                        else:
                            current_logger.info(f"Local file {local_file_path.name} exists but sizes differ or FTP size check failed. Re-downloading.")
                    except Exception as size_e:
                        current_logger.warning(f"Could not get remote FTP file size for {remote_file_path}: {size_e}. Assuming re-download is needed.")
            else:
                current_logger.info(f"Local file {local_file_path.name} is missing. Downloading.")

            if download_needed:
                current_logger.info(f"Downloading {remote_file_path} to {local_file_path}")
                try:
                    if protocol.lower() == 'sftp':
                        client.get(remote_file_path, str(local_file_path))
                    elif protocol.lower() == 'ftp':
                        with open(local_file_path, 'wb') as f:
                            # For FTP, ensure we are in the correct remote directory or use full path in RETR
                            # Assuming remote_file_path is already the full path for RETR
                            client.retrbinary(f"RETR {remote_file_path}", f.write)
                    current_logger.info(f"Successfully downloaded {local_file_path.name}")
                except FileNotFoundError:
                    current_logger.error(f"Remote file {remote_file_path} not found during download attempt. Skipping this specific file.")
                except Exception as download_e:
                    current_logger.error(f"Error downloading {remote_file_path} to {local_file_path}: {download_e}")
                    # Decide if you want to re-raise or just log and continue for other files

    except Exception as e:
        current_logger.error(f"An error occurred during {protocol.upper()} transfer process: {e}")
        raise

    finally:
        if client:
            if protocol.lower() == 'sftp' and ssh_client:
                ssh_client.close() # Close the SSH client, which closes the SFTP client
                current_logger.info("SFTP SSH client closed.")
            elif protocol.lower() == 'ftp':
                client.quit()
                current_logger.info("FTP client closed.")
        else:
            current_logger.warning(f"{protocol.upper()} client was not initialized or could not be closed.")

    current_logger.info(f"{protocol.upper()} file fetching process completed.")

