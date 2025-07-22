# src/pytaps/file_operations.py
import os
import fnmatch
import shutil
from datetime import datetime
import logging # <-- NEW: Import logging

logger = logging.getLogger(__name__) # <-- NEW: Get a logger for this module

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

def move_files_by_pattern(source_dir, filename_pattern, destination_dir):
    """
    Moves files matching a glob-style pattern from a source directory to a destination directory.

    Args:
        source_dir (str): The directory to search for files.
        filename_pattern (str): The glob-style pattern to match.
        destination_dir (str): The directory to move files to.

    Returns:
        list: A list of full paths of files that were successfully moved.

    Raises:
        FileNotFoundError: If the source directory does not exist.
    """
    logger.info(f"Attempting to move files matching '{filename_pattern}' from '{source_dir}' to '{destination_dir}'.")
    if not os.path.isdir(source_dir):
        logger.error(f"Source directory not found: {source_dir}")
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    os.makedirs(destination_dir, exist_ok=True) # Ensure destination exists
    logger.debug(f"Ensured destination directory exists: {destination_dir}")

    moved_files = []
    for filename in os.listdir(source_dir):
        if fnmatch.fnmatch(filename, filename_pattern):
            src_path = os.path.join(source_dir, filename)
            dest_path = os.path.join(destination_dir, filename)
            try:
                shutil.move(src_path, dest_path)
                moved_files.append(dest_path)
                logger.info(f"Successfully moved '{filename}' to '{destination_dir}'.")
            except Exception as e:
                logger.error(f"Error moving file '{src_path}' to '{dest_path}': {e}")
    logger.info(f"Finished moving {len(moved_files)} files.")
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
        # Open the output file in 'wb' mode (write binary)
        with open(output_filepath, "wb") as outfile:
            for input_file in input_filepaths:
                if os.path.exists(input_file):
                    logger.debug(f"Appending '{input_file}' to '{output_filepath}'.")
                    # Open each input file in 'rb' mode (read binary)
                    with open(input_file, "rb") as infile:
                        outfile.write(infile.read()) # Read all content and write it to the output
                else:
                    logger.warning(f"Input file '{input_file}' not found, skipping.")
        logger.info(f"Successfully merged files into '{output_filepath}'.")
        return output_filepath
    except IOError as e:
        logger.error(f"Error during binary file merging to '{output_filepath}': {e}")
        raise

def delete_files(file_paths, ignore_errors=True):
    """
    **What it does:** This function takes a list of file paths and removes (deletes) each of them.
    It's designed to clean up temporary or unneeded files from your computer.

    **Why it's in PyTAP:**
    *   **Reusable:** Almost every automated process creates temporary files that need to be removed later. This function provides a standard way to do that.
    *   **Safe Cleanup:** It checks if a file actually exists before trying to delete it, and it can be set to continue even if some files can't be deleted (e.g., due to permissions), logging the problem instead of stopping everything.
    *   **Simpler Code:** You can give it a whole list of files, and it handles deleting each one, making your cleanup code much shorter and easier to read.

    Args:
        file_paths (list): A list of paths to the files you want to delete.
        ignore_errors (bool): If True (default), the function will log any errors during deletion
                              but continue trying to delete other files. If False, it will stop
                              and raise an error immediately if a deletion fails.

    Returns:
        list: A list of paths to files that were successfully deleted.
    """
    deleted_count = 0
    successfully_deleted = []
    logger.info(f"Attempting to delete {len(file_paths)} files.")
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path) # This is the command that actually deletes the file
                logger.debug(f"Removed file: '{file_path}'")
                deleted_count += 1
                successfully_deleted.append(file_path)
            else:
                logger.warning(f"File not found, skipping deletion: '{file_path}'")
        except OSError as e: # Catch errors like permission denied
            logger.error(f"Error deleting file '{file_path}': {e}")
            if not ignore_errors:
                raise # If ignore_errors is False, stop here and raise the error
    logger.info(f"Successfully deleted {deleted_count} out of {len(file_paths)} files.")
    return successfully_deleted
