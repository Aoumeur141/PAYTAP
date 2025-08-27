# src/pytaps/file_operations.py
import os
import fnmatch
import shutil
from datetime import datetime
import logging

from pathlib import Path
from typing import List, Union, Optional


logger = logging.getLogger(__name__)

def generate_met_filename(date_obj):
    """
    Generates a meteorological filename string based on a date object.
    This is useful for common naming conventions like 'YYYYMMDD'.

    Args:
        date_obj (datetime.date or datetime.datetime): The date object to use.

    Returns:
        str: The formatted filename string, e.g., "*SP1*20231026000*".
    """
    file_date_str = date_obj.strftime("%Y%m%d")
    # This pattern is specific to meteorological data files.
    return f"*SP1*{file_date_str}000*"

def check_local_files_exist(local_dir, filename_pattern):
    """
    Checks if any files matching the glob-style pattern exist in the local directory.

    Args:
        local_dir (str): The local directory to check.
        filename_pattern (str): The glob-style pattern to match (e.g., "*SP1*20231026000*").

    Returns:
        bool: True if at least one matching file is found, False otherwise.
    """
    logger.debug(f"Checking for files matching '{filename_pattern}' in '{local_dir}'.")
    if not os.path.isdir(local_dir):
        logger.debug(f"Local directory '{local_dir}' does not exist.")
        return False

    for filename in os.listdir(local_dir):
        if fnmatch.fnmatch(filename, filename_pattern):
            logger.debug(f"Found matching file: '{filename}'")
            return True
    logger.debug(f"No files matching '{filename_pattern}' found in '{local_dir}'.")
    return False

def move_files_by_pattern(source_dir, filename_pattern, destination_dir, logger_instance=None):
    """
    Moves files matching a pattern from a source directory to a destination directory.

    Args:
        source_dir (str or Path): The directory to search for files.
        filename_pattern (str): The glob-style pattern to match files (e.g., "*.txt").
        destination_dir (str or Path): The directory to move the files to.
        logger_instance (logging.Logger, optional): An optional logger instance to use for logging.
                                                     If None, a default internal logger is used.

    Returns:
        list: A list of Path objects of the files that were moved.
    """
    current_function_logger = logger_instance if logger_instance is not None else logger # Use the module's 'logger'
    source_path = Path(source_dir)
    destination_path = Path(destination_dir)

    if not source_path.is_dir():
        current_function_logger.error(f"Source directory does not exist: {source_path}") # Use current_function_logger
        return []
    
    if not destination_path.is_dir():
        try:
            destination_path.mkdir(parents=True, exist_ok=True)
            current_function_logger.info(f"Created destination directory: {destination_path}") # Use current_function_logger
        except OSError as e:
            current_function_logger.error(f"Failed to create destination directory {destination_path}: {e}") # Use current_function_logger
            return []

    moved_files = []
    # FIX: Removed extra ')'
    current_function_logger.debug(f"Searching for files matching '{filename_pattern}' in '{source_path}'")
    
    # Use glob to find files matching the pattern
    found_files = list(source_path.glob(filename_pattern))

    if not found_files:
        current_function_logger.info(f"No files found matching pattern '{filename_pattern}' in '{source_path}'.") # Use current_function_logger
        return []

    for file_path in found_files:
        if file_path.is_file():
            try:
                shutil.move(str(file_path), str(destination_path / file_path.name))
                moved_files.append(destination_path / file_path.name)
                current_function_logger.info(f"Moved '{file_path.name}' to '{destination_path}'.") # Use current_function_logger
            except shutil.Error as e:
                current_function_logger.error(f"Error moving '{file_path.name}' to '{destination_path}': {e}") # Use current_function_logger
            except Exception as e:
                current_function_logger.error(f"An unexpected error occurred while moving '{file_path.name}': {e}", exc_info=True) # Use current_function_logger
        else:
            current_function_logger.debug(f"Skipping non-file item: {file_path}") # Use current_function_logger

    return moved_files


def merge_binary_files(output_filepath, input_filepaths):
    """
    **What it does:** This function takes a list of file paths and combines their raw (binary) content
    into a single new file. It's like sticking several pieces of a puzzle together to make one big piece.

    **Why it's in PyTAP:**
    *   **Reusable:** Many times, you'll have data split across several files (like parts of a large download or log files) that you need to combine into one. This function does that simply.
    *   **Simple to use:** You just give it the list of files to combine and the name for the new combined file. You don't need to worry about the technical details of reading and writing binary data.
    *   **Consistent:** Ensures that whenever you need to merge files in your projects, it's done in the same reliable way.

    Args:
        output_filepath (str): The path where the new combined file will be saved.
        input_filepaths (list): A list of paths to the files you want to combine.

    Returns:
        str: The path to the created combined file.

    Raises:
        IOError: If there's a problem reading an input file or writing to the output file.
    """
    logger.info(f"Starting merge of {len(input_filepaths)} files into '{output_filepath}'.")
    try:
        ## Open the output file in 'wb' mode (write binary)
        with open(output_filepath, "wb") as outfile:
            for input_file in input_filepaths:
                if os.path.exists(input_file):
                    logger.debug(f"Appending '{input_file}' to '{output_filepath}'.")
                    ## Open each input file in 'rb' mode (read binary)
                    with open(input_file, "rb") as infile:
                        outfile.write(infile.read()) ## Read all content and write it to the output
                else:
                    logger.warning(f"Input file '{input_file}' not found, skipping.")
        logger.info(f"Successfully merged files into '{output_filepath}'.")
        return output_filepath
    except IOError as e:
        logger.error(f"Error during binary file merging to '{output_filepath}': {e}")
        raise

# This is the CORRECTED and KEPT version of delete_files
def delete_files(file_paths, ignore_errors=False, logger_instance=None):
    """
    Deletes a list of specified files.

    Args:
        file_paths (list): A list of file paths (str or Path objects) to delete.
        ignore_errors (bool): If True, continue deleting other files even if one fails.
                              If False, stop and raise an exception on the first failure.
        logger_instance (logging.Logger, optional): An optional logger instance to use for logging.
                                                     If None, a default internal logger is used.

    Returns:
        bool: True if all files were successfully deleted (or ignored if ignore_errors is True), False otherwise.
    """
    current_function_logger = logger_instance if logger_instance is not None else logger # Use the module's 'logger'
    
    success = True
    for file_path in file_paths:
        path = Path(file_path)
        if path.exists():
            try:
                if path.is_file():
                    os.remove(path)
                    current_function_logger.info(f"Successfully deleted file: {path}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    current_function_logger.info(f"Successfully deleted directory and its contents: {path}")
                else:
                    current_function_logger.warning(f"Path is not a file or directory, skipping: {path}")
            except OSError as e:
                current_function_logger.error(f"Error deleting {path}: {e}")
                if not ignore_errors:
                    success = False
                    raise # Re-raise if not ignoring errors
            except Exception as e:
                current_function_logger.error(f"An unexpected error occurred while deleting {path}: {e}", exc_info=True)
                if not ignore_errors:
                    success = False
                    raise
        else:
            current_function_logger.debug(f"File not found, skipping deletion: {path}")
    return success

def build_time_series_filepath(
    base_dir: Union[str, Path],
    year: str,
    month: str,
    day: str,
    hour: int,
    filename_prefix: str,
    filename_suffix: str
) -> Path:
    """
    Constructs a file path for time-series data with a YYYY/MM/DD directory structure.
    This simplifies repetitive path construction for dated files.

    Args:
        base_dir (Union[str, Path]): The base directory where the time-series data is stored.
        year (str): The year (e.g., '2023').
        month (str): The month (e.g., '01').
        day (str): The day (e.g., '15').
        hour (int): The hour (0-23).
        filename_prefix (str): Prefix for the filename (e.g., 'Synop_').
        filename_suffix (str): Suffix for the filename (e.g., '.bufr').

    Returns:
        Path: The constructed absolute file path using pathlib.
    """
    base_path = Path(base_dir).resolve()
    ## use path module from pathlib to resolve the path that mean remove ../ for linux and ./ for windows to get the full absolut path

    # Using f-strings for consistent filename formatting
    file_path = base_path / year / month / day / f"{filename_prefix}{year}{month}{day}{hour:02d}00{filename_suffix}"
    logger.debug(f"Constructed file path: {file_path}")
    return file_path



def check_file_exists_and_log(file_path: Union[str, Path], logger_instance: Optional[logging.Logger] = None) -> bool:
    """
    Checks if a file exists and logs a warning if it does not.
    This simplifies repetitive file existence checks and consistent logging.

    Args:
        file_path (Union[str, Path]): The path to the file to check.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use for messages.
                                                     If None, the module's default logger is used.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    path = Path(file_path)
    if not path.exists():
        current_logger.warning(f"File not found: {path}. Skipping this operation.")
        return False
    current_logger.debug(f"File found: {path}")
    return True


def clean_directory(
    directory_path: Union[str, Path],
    file_pattern: Optional[str] = None,
    ignore_errors: bool = True,
    logger_instance: Optional[logging.Logger] = None
) -> List[Path]:
    """
    Deletes files within a specified directory. Can optionally filter by a glob-style pattern.

    Args:
        directory_path (Union[str, Path]): The path to the directory to clean.
        file_pattern (Optional[str]): A glob-style pattern (e.g., '*.tmp', 'prefix*') to match files.
                                      If None, all files in the directory will be considered for deletion.
        ignore_errors (bool): If True, logs errors during deletion but continues. If False, raises
                              the first OSError encountered.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use for messages.
                                                     If None, the module's default logger is used.

    Returns:
        List[Path]: A list of paths to files that were successfully deleted.

    Raises:
        FileNotFoundError: If the specified directory does not exist.
        OSError: If `ignore_errors` is False and a file deletion fails.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    dir_path = Path(directory_path).resolve()

    if not dir_path.exists():
        current_logger.warning(f"Directory not found: {dir_path}. Skipping cleanup.")
        return []
    if not dir_path.is_dir():
        current_logger.error(f"Path is not a directory: {dir_path}. Cannot clean.")
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")

    current_logger.info(f"Starting cleanup of directory: {dir_path} (Pattern: {file_pattern if file_pattern else 'All files'})")
    
    deleted_files = []
    for item in dir_path.iterdir():
        if item.is_file():
            if file_pattern is None or fnmatch.fnmatch(item.name, file_pattern):
                try:
                    item.unlink() # Delete the file
                    deleted_files.append(item)
                    current_logger.debug(f"Deleted file: {item}")
                except OSError as e:
                    current_logger.error(f"Error deleting file '{item}': {e}")
                    if not ignore_errors:
                        raise # Re-raise if not ignoring errors
        else:
            current_logger.debug(f"Skipping non-file entry: {item}")

    current_logger.info(f"Finished cleanup. Successfully deleted {len(deleted_files)} files from {dir_path}.")
    return deleted_files


def copy_directory_recursive(
    source_dir: Union[str, Path],
    destination_dir: Union[str, Path],
    overwrite_existing: bool = True, # New parameter to control overwrite behavior
    ignore_errors: bool = False, # Consistent with other functions, though shutil.copytree has its own error handling
    logger_instance: Optional[logging.Logger] = None
) -> Optional[Path]:
    """
    Recursively copies a directory from source to destination.
    If overwrite_existing is True and destination exists, it will be removed first.

    Args:
        source_dir (Union[str, Path]): The path to the source directory.
        destination_dir (Union[str, Path]): The path to the destination directory.
        overwrite_existing (bool): If True, and destination_dir exists, it will be
                                   deleted before copying. If False, and destination_dir
                                   exists, an error will be raised by shutil.copytree.
                                   Defaults to True to mimic 'cp -r' behavior.
        ignore_errors (bool): If True, errors during directory removal (if overwriting)
                              or copying will be logged but not re-raised. Note that
                              shutil.copytree has its own error handling.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.
                                                     If None, the module's default logger is used.

    Returns:
        Optional[Path]: The path to the destination directory if successful, None otherwise.

    Raises:
        FileNotFoundError: If the source directory does not exist.
        OSError: If ignore_errors is False and an error occurs during copy or removal.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    src_path = Path(source_dir).resolve()
    dest_path = Path(destination_dir).resolve()

    current_logger.info(f"Attempting to copy directory from '{src_path}' to '{dest_path}'.")

    if not src_path.exists():
        current_logger.error(f"Source directory not found: {src_path}")
        if not ignore_errors:
            raise FileNotFoundError(f"Source directory not found: {src_path}")
        return None
    if not src_path.is_dir():
        current_logger.error(f"Source path is not a directory: {src_path}")
        if not ignore_errors:
            raise NotADirectoryError(f"Source path is not a directory: {src_path}")
        return None

    try:
        if dest_path.exists():
            if overwrite_existing:
                current_logger.info(f"Destination directory '{dest_path}' exists. Removing it before copying.")
                try:
                    shutil.rmtree(dest_path)
                    current_logger.debug(f"Successfully removed existing destination directory: {dest_path}")
                except OSError as e:
                    current_logger.error(f"Error removing existing destination directory '{dest_path}': {e}")
                    if not ignore_errors:
                        raise
            else:
                current_logger.error(f"Destination directory '{dest_path}' already exists and overwrite_existing is False.")
                if not ignore_errors:
                    raise FileExistsError(f"Destination directory '{dest_path}' already exists.")
                return None

        shutil.copytree(src_path, dest_path)
        current_logger.info(f"Successfully copied directory from '{src_path}' to '{dest_path}'.")
        return dest_path
    except Exception as e:
        current_logger.error(f"An error occurred during recursive directory copy from '{src_path}' to '{dest_path}': {e}", exc_info=True)
        if not ignore_errors:
            raise
        return None


def ensure_parent_directory_exists(file_path: Union[str, Path], logger_instance: Optional[logging.Logger] = None) -> None:
    """
    Ensures that the parent directory for a given file path exists.
    Creates it if it doesn't, including any necessary intermediate directories.

    Args:
        file_path (Union[str, Path]): The path to the file whose parent directory needs to exist.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.
                                                     If None, the module's default logger is used.
    Raises:
        OSError: If the directory cannot be created.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    path = Path(file_path)
    parent_dir = path.parent

    if not parent_dir.exists():
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
            current_logger.debug(f"Created parent directory: {parent_dir}")
        except OSError as e:
            current_logger.error(f"Failed to create directory {parent_dir}: {e}")
            raise
    else:
        current_logger.debug(f"Parent directory already exists: {parent_dir}")
