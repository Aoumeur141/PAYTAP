# pytaps/config_utils.py
import json
import os
import sys
import logging
from typing import Dict, Any, Optional

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
        ##_logger.info(f"Configuration loaded successfully from: {config_file_path}")
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
    Extracts and validates FTP settings from the loaded configuration.
    This function specifically validates the structure required by pytaps's fetchdata.

    Args:
        config (Dict[str, Any]): The full configuration dictionary loaded from JSON.

    Returns:
        Dict[str, Any]: A dictionary containing validated FTP settings.
                        Includes 'port' which defaults to None if not specified.

    Raises:
        ValueError: If the 'ftp' section or any required FTP keys are missing or invalid.
    """
    if 'ftp' not in config:
        raise ValueError("Missing required 'ftp' section in configuration.")

    ftp_config = config['ftp']
    required_ftp_keys = ['host', 'username', 'password', 'remote_base_directory']
    extracted_settings = {}

    for key in required_ftp_keys:
        if key not in ftp_config:
            raise ValueError(f"Missing required FTP configuration key: 'ftp.{key}'.")
        if not isinstance(ftp_config[key], str):
            _logger.warning(f"FTP key 'ftp.{key}' is not a string. Attempting to convert.")
            try:
                extracted_settings[key] = str(ftp_config[key])
            except Exception:
                raise ValueError(f"FTP key 'ftp.{key}' must be a string and could not be converted.")
        else:
            extracted_settings[key] = ftp_config[key]

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
    Extracts and validates SFTP settings from the loaded configuration.
    This function specifically validates the structure required by pytaps's fetchdata.

    Args:
        config (Dict[str, Any]): The full configuration dictionary loaded from JSON.

    Returns:
        Dict[str, Any]: A dictionary containing validated SFTP settings.

    Raises:
        ValueError: If the 'sftp' section or any required SFTP keys are missing or invalid.
    """
    if 'sftp' not in config:
        raise ValueError("Missing required 'sftp' section in configuration.")

    sftp_config = config['sftp']
    required_sftp_keys = ['host', 'username', 'password', 'port']
    extracted_settings = {}

    for key in required_sftp_keys:
        if key not in sftp_config:
            raise ValueError(f"Missing required SFTP configuration key: 'sftp.{key}'.")
        if not isinstance(sftp_config[key], (str, int)): # Port can be int
            raise ValueError(f"SFTP key 'sftp.{key}' must be a string or integer.")
        extracted_settings[key] = sftp_config[key]

    # Ensure port is an integer
    if not isinstance(extracted_settings['port'], int):
        try:
            extracted_settings['port'] = int(extracted_settings['port'])
        except (ValueError, TypeError):
            raise ValueError(f"SFTP port 'sftp.port' must be an integer or convertible to an integer.")

    return extracted_settings


def get_logging_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and validates logging settings from the loaded configuration.
    This function specifically validates the structure required by pytaps's logging_utils.
    Additionally, it updates the internal _logger's level to match the configuration.

    Args:
        config (Dict[str, Any]): The full configuration dictionary loaded from JSON.

    Returns:
        Dict[str, Any]: A dictionary containing validated logging settings,
                        with 'log_level' converted to its logging module constant.

    Raises:
        ValueError: If the 'logging' section or any required logging keys are missing or invalid.
    """
    if 'logging' not in config:
        raise ValueError("Missing required 'logging' section in configuration.")

    logging_config = config['logging']
    required_logging_keys = ['log_file_base_name', 'log_level']
    extracted_settings = {}

    for key in required_logging_keys:
        if key not in logging_config:
            raise ValueError(f"Missing required logging configuration key: 'logging.{key}'.")
        if not isinstance(logging_config[key], str):
            raise ValueError(f"Logging key 'logging.{key}' must be a string.")
        extracted_settings[key] = logging_config[key]

    # Convert log_level string to logging constant
    log_level_str = extracted_settings['log_level'].upper()
    log_level = getattr(logging, log_level_str, None)
    if log_level is None:
        raise ValueError(f"Invalid log level specified: '{extracted_settings['log_level']}'. "
                         f"Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.")
    extracted_settings['log_level'] = log_level

    # --- NEW: Update the internal _logger's level based on the loaded config ---
    # This ensures config_utils's own logger respects the application's configured level
    _logger.setLevel(log_level)
    _logger.debug(f"Internal config_utils logger level updated to: {log_level_str}")

    return extracted_settings


def get_arpege_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and validates ARPEGE-specific settings from the loaded configuration.
    """
    if 'arpege' not in config:
        raise ValueError("Missing required 'arpege' section in configuration.")

    arpege_config = config['arpege']
    if 'expected_forecast_steps' not in arpege_config or not isinstance(arpege_config['expected_forecast_steps'], list):
        raise ValueError("Missing or invalid 'arpege.expected_forecast_steps' in configuration (must be a list).")

    return arpege_config # No further validation needed for now, just return the dict


def get_aladin_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and validates ALADIN-specific settings from the loaded configuration.
    """
    if 'aladin' not in config:
        raise ValueError("Missing required 'aladin' section in configuration.")

    aladin_config = config['aladin']
    required_aladin_keys = [
        'remote_path_template', 'local_temp_subdir',
        'filename_pattern_template', 'ech_ranges'
    ]
    for key in required_aladin_keys:
        if key not in aladin_config:
            raise ValueError(f"Missing required ALADIN configuration key: 'aladin.{key}'.")

    if not isinstance(aladin_config['ech_ranges'], list) or len(aladin_config['ech_ranges']) != 3:
        raise ValueError("ALADIN 'ech_ranges' must be a list of 3 integers (start, end, step).")
    if not all(isinstance(x, int) for x in aladin_config['ech_ranges']):
        raise ValueError("ALADIN 'ech_ranges' must contain only integers.")

    return aladin_config


def get_app_settings(config: Dict[str, Any], section_name: str) -> Dict[str, Any]:
    """
    Extracts a specific application-defined section from the loaded configuration.
    Performs basic check for section existence. Further validation of keys
    within the section should be handled by the calling application.

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
    return config[section_name]
