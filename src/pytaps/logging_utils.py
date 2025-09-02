import os
import logging
import sys

def setup_logger(script_name: str, log_directory_base: str = None, log_level=logging.INFO, shared_log_file_path: str = None, force_new_log: bool = False):
    """
    Sets up the root logger for the application, ensuring consistent logging patterns
    and dynamic log file naming. Can be configured for a single log file across chained scripts.
    It now includes an option to force a new log file, clearing previous content.

    Args:
        script_name (str): The name of the script (e.g., "my_script.py").
                           This will be used to name the log file if shared_log_file_path is None.
        log_directory_base (str, optional): The absolute path to the directory where the
                                            'logs' folder should be created.
                                            If None, it defaults to the directory of the
                                            main script being executed. This is used if
                                            shared_log_file_path is None.
        log_level (int, optional): The logging level (e.g., logging.INFO, logging.DEBUG).
                                   Defaults to logging.INFO.
        shared_log_file_path (str, optional): An explicit, absolute path to a log file
                                              to be used. If provided, this overrides
                                              log_directory_base and script_name for file logging.
                                              Useful for chaining scripts into a single log.
                                              If not provided, it will check the 'SHARED_LOG_FILE'
                                              environment variable.
        force_new_log (bool, optional): If True, the log file will be truncated (cleared)
                                        at the start of this logger setup, effectively
                                        starting a fresh log. If False, the behavior depends:
                                        - For individual script logs (not shared), it defaults to 'w' (new log).
                                        - For shared log files, it defaults to 'a' (append).
                                        Defaults to False.

    Returns:
        tuple[logging.Logger, str]: A tuple containing the configured root logger instance
                                    and the full path to the log file being used.
    """
    # Try to get shared log file path from argument, then from environment variable
    final_log_file_path = shared_log_file_path
    if not final_log_file_path:
        final_log_file_path = os.environ.get('SHARED_LOG_FILE')

    is_shared_log = bool(final_log_file_path) # Flag to indicate if we are using a shared log

    if is_shared_log:
        log_file_path = final_log_file_path
        # Ensure the directory for the shared log file exists
        log_dir = os.path.dirname(log_file_path)
        os.makedirs(log_dir, exist_ok=True)
    else:
        # Determine the base directory for logs if no shared path is provided.
        if log_directory_base is None:
            # Use the directory of the main script being executed
            log_directory_base = os.path.dirname(os.path.abspath(sys.argv[0]))

        # Define the log directory and file path for individual script logging
        log_dir = os.path.join(log_directory_base, "logs")
        log_file_name = f"{script_name}.log"
        log_file_path = os.path.join(log_dir, log_file_name)

        # Create the log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

    # Determine the file handler mode:
    # - If force_new_log is True, always use 'w' (write/truncate).
    # - If force_new_log is False:
    #   - For individual script logs (not shared), use 'w' to start a fresh log for each run.
    #   - For shared log files, use 'a' (append) to collect logs from multiple scripts.
    file_handler_mode = 'w' if force_new_log or not is_shared_log else 'a'

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers from the root logger to prevent duplicates
    # This is crucial for shared logging to prevent multiple handlers writing to the same file
    # or to prevent previous handlers from writing to old files.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a file handler with the determined mode
    file_handler = logging.FileHandler(log_file_path, mode=file_handler_mode)
    file_handler.setLevel(log_level)

    # Create a console handler (explicitly using sys.stdout for clarity)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create a formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger, log_file_path
