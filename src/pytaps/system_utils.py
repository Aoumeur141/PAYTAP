# src/pytaps/system_utils.py
import subprocess
import logging
import os # <-- Needed for os.path.exists if you want to check command path

logger = logging.getLogger(__name__) # Get a logger for this module

def execute_command(command, check=True, capture_output=True, text=True, cwd=None):
    """
    **What it does:** This function runs a command or program on your computer (like 'grib_copy' or 'ls').
    It waits for the command to finish and tells you if it worked or failed.

    **Why it's in PyTAP:**
    *   **Reusable:** Many automated tasks involve running other programs (e.g., converting files, compressing data, fetching information). This function provides a safe and consistent way to do that.
    *   **Error Handling:** It automatically checks if the command ran successfully. If something goes wrong (like the program not being found or crashing), it logs the error and can stop your script, preventing bigger problems.
    *   **Cleaner Code:** Instead of writing complex `try-except` blocks and `subprocess.run` calls every time, you just call this one function, making your main application code much neater.
    *   **Current Working Directory (cwd):** You can tell it *where* to run the command, which is safer than changing your script's main directory with `os.chdir()`.

    Args:
        command (list): The command and its parts as a list (e.g., ["grib_copy", "-w", "shortName=2t", "input.grib", "output.grib"]).
        check (bool): If True (default), the function will stop and raise an error if the command fails (returns a non-zero code).
        capture_output (bool): If True (default), the function will collect any text the command prints to the screen (output and errors).
        text (bool): If True (default), the captured output will be treated as regular text (strings).
        cwd (str, optional): The directory where the command should be run. If not provided, it runs in the current directory of your Python script.

    Returns:
        subprocess.CompletedProcess: An object containing information about the finished command (like its output and error messages).

    Raises:
        subprocess.CalledProcessError: If 'check' is True and the command fails.
        FileNotFoundError: If the command itself (e.g., 'grib_copy') cannot be found on your system.
    """
    command_str = ' '.join(command) # Just for logging, makes the command easy to read
    logger.info(f"Executing command: {command_str}")
    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=capture_output,
            text=text,
            cwd=cwd # Run the command in this specific directory
        )
        logger.info(f"Command '{command[0]}' completed successfully.")
        # Log any output from the command for debugging
        if result.stdout:
            logger.debug(f"STDOUT: {result.stdout.strip()}")
        if result.stderr:
            logger.debug(f"STDERR: {result.stderr.strip()}")
        return result
    except FileNotFoundError:
        logger.error(f"Command '{command[0]}' not found. Make sure it's installed and in your system's PATH, or provide its full path.")
        raise # Re-raise the error so your main application knows it failed
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{command_str}' failed with exit code {e.returncode}.")
        logger.error(f"STDOUT: {e.stdout.strip()}")
        logger.error(f"STDERR: {e.stderr.strip()}")
        raise # Re-raise the error
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred while executing '{command_str}': {e}")
        raise # Re-raise the error
