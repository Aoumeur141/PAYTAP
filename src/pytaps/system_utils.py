# src/pytaps/system_utils.py
import subprocess
import logging
import os # <-- Needed for os.path.exists if you want to check command path
from pathlib import Path # Good practice for path manipulation

# Get a default logger for this module. This will be used if no specific logger
# is passed to the function.
_default_logger = logging.getLogger(__name__)

def execute_command(command, check=True, capture_output=True, text=True, cwd=None, logger_instance=None, env=None):
    """
    Executes a shell command and logs its output.

    Args:
        command (list): The command and its parts as a list.
        check (bool): If True, raise CalledProcessError for non-zero exit codes.
        capture_output (bool): If True, capture stdout and stderr.
        text (bool): If True, decode stdout/stderr as text.
        cwd (str or Path, optional): The current working directory for the command.
        logger_instance (logging.Logger, optional): An optional logger instance.
        env (dict, optional): A dictionary of environment variables to set for the new process.
                              If None, the current environment variables are inherited.

    Returns:
        subprocess.CompletedProcess: An object containing information about the finished command.

    Raises:
        subprocess.CalledProcessError: If 'check' is True and the command fails.
        FileNotFoundError: If the command executable is not found.
        Exception: For other unexpected errors during execution.
    """
    current_logger = logger_instance if logger_instance is not None else _default_logger

    command_str = ' '.join(command)
    current_logger.info(f"Executing command: {command_str} in directory: '{cwd if cwd else Path.cwd()}'")

    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=capture_output,
            text=text,
            cwd=cwd,
            env=env # <--- Pass the environment variables here
        )
        current_logger.info(f"Command '{command[0]}' completed successfully.")
        if result.stdout:
            current_logger.debug(f"STDOUT: {result.stdout.strip()}")
        if result.stderr:
            current_logger.debug(f"STDERR: {result.stderr.strip()}")
        return result
    except FileNotFoundError:
        current_logger.error(f"Command '{command[0]}' not found. Make sure it's installed and in your system's PATH, or provide its full path.")
        raise
    except subprocess.CalledProcessError as e:
        current_logger.error(f"Command '{command_str}' failed with exit code {e.returncode}.")
        current_logger.error(f"STDOUT: {e.stdout.strip()}")
        current_logger.error(f"STDERR: {e.stderr.strip()}")
        raise
    except Exception as e:
        current_logger.critical(f"An unexpected error occurred while executing '{command_str}': {e}", exc_info=True)
        raise


