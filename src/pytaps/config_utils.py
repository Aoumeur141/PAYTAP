# pytaps/config_utils.py
import json
import os
import sys
import logging
from typing import Dict, Any, Optional, List

# A basic logger for this utility, to report errors before the main application logger is set up.
# This ensures that configuration loading errors are always visible.
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO) # Initial level for config loading (e.g., to log 'Configuration loaded successfully')
if not _logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    _logger.addHandler(handler)


def load_configuration(config_file_path: str) -> Dict[str, Any]:
    """
    Loads configuration from a JSON file. This function is generic and does not
    validate the content of the JSON, allowing for flexible configuration structures.
    It returns the raw dictionary, and specific validation/extraction should be
    handled by dedicated functions or the calling script.

    Args:
        config_file_path (str): The full path to the configuration JSON file.

    Returns:
        Dict[str, Any]: A dictionary containing the loaded configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        json.JSONDecodeError: If the configuration file is not valid JSON.
        Exception: For any other unexpected errors during file loading.
    """
    if not os.path.exists(config_file_path):
        _logger.error(f"Configuration file not found at: {config_file_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_file_path}")

    try:
        with open(config_file_path, 'r') as f:
            config = json.load(f)
        _logger.info(f"Configuration loaded successfully from: {config_file_path}")
        return config
    except json.JSONDecodeError as e:
        _logger.error(f"Error decoding JSON from {config_file_path}: {e}")
        # Re-raise the original exception for specific handling upstream
        raise
    except Exception as e:
        _logger.error(f"An unexpected error occurred while loading configuration from {config_file_path}: {e}")
        raise


def get_ftp_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and validates core FTP settings from the loaded configuration.
    This function ensures essential keys required by pytaps's fetchdata are present
    and returns all settings found in the 'ftp' section.

    Args:
        config (Dict[str, Any]): The full configuration dictionary loaded from JSON.

    Returns:
        Dict[str, Any]: A dictionary containing validated FTP settings.
                        Includes all other keys found in the 'ftp' section.

    Raises:
        ValueError: If the 'ftp' section or any core required FTP keys are missing or invalid.
    """
    if 'ftp' not in config:
        raise ValueError("Missing required 'ftp' section in configuration.")

    ftp_config = config['ftp']
    # Start by copying all settings from the config file's 'ftp' section
    extracted_settings = ftp_config.copy()

    # Define truly CORE required keys for pytaps's FTP operations
    core_required_ftp_keys = ['host', 'username', 'password', 'remote_base_directory']

    for key in core_required_ftp_keys:
        if key not in ftp_config:
            raise ValueError(f"Missing required FTP configuration key: 'ftp.{key}'.")
        if not isinstance(ftp_config[key], str):
            _logger.warning(f"FTP key 'ftp.{key}' is not a string. Attempting to convert.")
            try:
                extracted_settings[key] = str(ftp_config[key])
            except Exception:
                raise ValueError(f"FTP key 'ftp.{key}' must be a string and could not be converted.")
        else:
            extracted_settings[key] = ftp_config[key] # Ensure it's in extracted_settings if it wasn't already

    # Handle 'port' specifically, allowing it to be optional and default to None
    port_value = ftp_config.get('port')
    if port_value is not None:
        if not isinstance(port_value, int):
            try:
                port_value = int(port_value)
            except (ValueError, TypeError):
                raise ValueError(f"FTP port 'ftp.port' must be an integer or convertible to an integer if specified.")
        extracted_settings['port'] = port_value
    else:
        extracted_settings['port'] = None # Explicitly set to None if not present

    return extracted_settings


def get_sftp_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and validates core SFTP settings from the loaded configuration.
    This function ensures essential keys required by pytaps's fetchdata are present
    and returns all settings found in the 'sftp' section.

    Args:
        config (Dict[str, Any]): The full configuration dictionary loaded from JSON.

    Returns:
        Dict[str, Any]: A dictionary containing validated SFTP settings.
                        Includes all other keys found in the 'sftp' section.

    Raises:
        ValueError: If the 'sftp' section or any core required SFTP keys are missing or invalid.
    """
    if 'sftp' not in config:
        raise ValueError("Missing required 'sftp' section in configuration.")

    sftp_config = config['sftp']
    # Start by copying all settings from the config file's 'sftp' section
    extracted_settings = sftp_config.copy()

    # Define truly CORE required keys for pytaps's SFTP operations
    core_required_sftp_keys = ['host', 'username', 'password', 'port']

    for key in core_required_sftp_keys:
        if key not in sftp_config:
            raise ValueError(f"Missing required SFTP configuration key: 'sftp.{key}'.")
        # Port is handled separately for int conversion
        if key != 'port' and not isinstance(sftp_config[key], str):
            raise ValueError(f"SFTP key 'sftp.{key}' must be a string.")
        # Ensure it's in extracted_settings if it wasn't already (e.g., after copy)
        extracted_settings[key] = sftp_config[key]

    # Ensure port is an integer
    if 'port' in extracted_settings:
        if not isinstance(extracted_settings['port'], int):
            try:
                extracted_settings['port'] = int(extracted_settings['port'])
            except (ValueError, TypeError):
                raise ValueError(f"SFTP port 'sftp.port' must be an integer or convertible to an integer.")
    else:
        raise ValueError("Missing required SFTP configuration key: 'sftp.port'.")

    return extracted_settings


def get_logging_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and validates logging settings from the loaded configuration.
    This function ensures core logging settings (for pytaps's internal logger setup)
    are present and valid, and returns all settings found in the 'logging' section,
    with 'log_level' converted to its logging module constant.

    Args:
        config (Dict[str, Any]): The full configuration dictionary loaded from JSON.

    Returns:
        Dict[str, Any]: A dictionary containing validated logging settings,
                        with 'log_level' converted to its logging module constant.
                        Includes all other keys found in the 'logging' section.

    Raises:
        ValueError: If the 'logging' section or any core required logging keys are missing or invalid.
    """
    if 'logging' not in config:
        raise ValueError("Missing required 'logging' section in configuration.")

    logging_config = config['logging']
    # Start by copying all settings from the config file's 'logging' section
    extracted_settings = logging_config.copy()

    # Define truly CORE required keys for pytaps's logging_utils.setup_logger
    # These are the absolute minimum for the logger to function.
    core_required_logging_keys = ['log_file_base_name', 'log_level']

    # Validate that the core required keys are present and are strings (except log_level for conversion)
    for key in core_required_logging_keys:
        if key not in logging_config:
            raise ValueError(f"Missing required logging configuration key: 'logging.{key}'.")
        if key != 'log_level' and not isinstance(logging_config[key], str):
            raise ValueError(f"Logging key 'logging.{key}' must be a string.")
        # Ensure it's in extracted_settings if it wasn't already (e.g., after copy)
        extracted_settings[key] = logging_config[key]

    # Convert log_level string to logging module constant
    log_level_str = extracted_settings['log_level'].upper()
    log_level = getattr(logging, log_level_str, None)
    if log_level is None:
        raise ValueError(f"Invalid log level specified: '{extracted_settings['log_level']}'. "
                         f"Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.")
    extracted_settings['log_level'] = log_level # Update with the logging constant

    # Update the internal _logger's level based on the loaded config
    _logger.setLevel(log_level)
    _logger.debug(f"Internal config_utils logger level updated to: {log_level_str}")

    # Return the complete dictionary, including all keys from the 'logging' section
    # found in config.json, after validating core ones and converting log_level.
    return extracted_settings


def get_arpege_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and validates ARPEGE-specific settings from the loaded configuration.
    Returns all settings found in the 'arpege' section.
    """
    if 'arpege' not in config:
        raise ValueError("Missing required 'arpege' section in configuration.")

    arpege_config = config['arpege']
    extracted_settings = arpege_config.copy() # Copy all settings

    # Validate core requirements for ARPEGE
    if 'expected_forecast_steps' not in arpege_config or not isinstance(arpege_config['expected_forecast_steps'], list):
        raise ValueError("Missing or invalid 'arpege.expected_forecast_steps' in configuration (must be a list).")
    # Further validation of list contents could be added if needed

    return extracted_settings


def get_aladin_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and validates ALADIN-specific settings from the loaded configuration.
    Returns all settings found in the 'aladin' section.
    """
    if 'aladin' not in config:
        raise ValueError("Missing required 'aladin' section in configuration.")

    aladin_config = config['aladin']
    extracted_settings = aladin_config.copy() # Copy all settings

    # Define truly CORE required keys for ALADIN operations
    core_required_aladin_keys = [
        'remote_path_template', 'local_temp_subdir',
        'filename_pattern_template', 'ech_ranges'
    ]

    for key in core_required_aladin_keys:
        if key not in aladin_config:
            raise ValueError(f"Missing required ALADIN configuration key: 'aladin.{key}'.")
        # Basic type check for string keys
        if key != 'ech_ranges' and not isinstance(aladin_config[key], str):
            raise ValueError(f"ALADIN key 'aladin.{key}' must be a string.")
        extracted_settings[key] = aladin_config[key] # Ensure it's in extracted_settings

    # Specific validation for 'ech_ranges'
    if not isinstance(extracted_settings['ech_ranges'], list) or len(extracted_settings['ech_ranges']) != 3:
        raise ValueError("ALADIN 'ech_ranges' must be a list of 3 integers (start, end, step).")
    if not all(isinstance(x, int) for x in extracted_settings['ech_ranges']):
        raise ValueError("ALADIN 'ech_ranges' must contain only integers.")

    return extracted_settings


def get_app_settings(config: Dict[str, Any], section_name: str) -> Dict[str, Any]:
    """
    Extracts a specific application-defined section from the loaded configuration.
    Performs basic check for section existence. This function is designed to be
    generic and flexible, returning the entire section as-is.
    Further validation of keys within the section should be handled by the
    calling application if specific keys are required.

    Args:
        config (Dict[str, Any]): The full configuration dictionary loaded from JSON.
        section_name (str): The name of the section to extract (e.g., 'bqrm_ref_app').

    Returns:
        Dict[str, Any]: A dictionary containing the settings for the specified section.

    Raises:
        ValueError: If the specified section is missing from the configuration.
    """
    if section_name not in config:
        raise ValueError(f"Missing required '{section_name}' section in configuration.")
    return config[section_name].copy() # Return a copy to prevent external modification of original config


def get_email_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and validates core email configuration settings (SMTP details, sender/receiver).
    This function ensures essential keys required for sending email are present
    and returns all settings found in the 'email' section.
    Application-specific email templates or content should be retrieved directly
    from the returned dictionary by the calling script.

    Args:
        config (Dict[str, Any]): The full configuration dictionary.

    Returns:
        Dict[str, Any]: A dictionary containing validated core email settings.
                        Includes all other keys found in the 'email' section.

    Raises:
        ValueError: If any core required email setting is missing or invalid.
    """
    if 'email' not in config:
        raise ValueError("Missing required 'email' section in configuration.")

    email_config = config.get('email', {})
    extracted_settings = email_config.copy() # Copy all settings

    # Define only the core email sending keys that are universally required by pytaps's email utility
    core_required_email_keys = [
        'sender_email',
        'receiver_emails',
        'password',
        'smtp_server',
        'smtp_port'
    ]

    # Validate presence of all core required keys
    for key in core_required_email_keys:
        if key not in email_config:
            raise ValueError(f"Missing required key '{key}' in 'email' section of configuration.")
        extracted_settings[key] = email_config[key] # Ensure it's in extracted_settings

    # --- Specific type/format validation for core settings ---
    if not isinstance(extracted_settings['sender_email'], str) or '@' not in extracted_settings['sender_email']:
        raise ValueError("Invalid 'sender_email' in 'email' section. Must be a valid email string.")
    if not isinstance(extracted_settings['receiver_emails'], list) or not all(isinstance(r, str) for r in extracted_settings['receiver_emails']):
        raise ValueError("Invalid 'receiver_emails' in 'email' section. Must be a list of email strings.")
    if not isinstance(extracted_settings['smtp_server'], str) or not extracted_settings['smtp_server']:
        raise ValueError("Invalid 'smtp_server' in 'email' section. Must be a non-empty string.")
    if not isinstance(extracted_settings['smtp_port'], int) or not (1 <= extracted_settings['smtp_port'] <= 65535):
        raise ValueError("Invalid 'smtp_port' in 'email' section. Must be an integer between 1 and 65535.")
    if not isinstance(extracted_settings['password'], str):
        # Password can be empty if using other auth methods, but should be a string
        raise ValueError("Invalid 'password' in 'email' section. Must be a string.")

    return extracted_settings
