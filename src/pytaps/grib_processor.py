# ~/bqrm/BMSLA/pytaps/grib_processor.py

import os
import logging
from typing import Union, Optional, List, Dict, Any, Tuple
import pdbufr
import epygram
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import subprocess

# Import necessary functions from other pytap modules
from .system_utils import execute_command
from .file_operations import merge_binary_files, delete_files

# Define a module-level logger. This will be used if no specific logger is passed to functions.
module_logger = logging.getLogger(__name__)
module_logger.propagate = False # Prevent messages from being passed to ancestor loggers

# --- REMOVE THIS DEBUGGING LINE ---
# import sys
# import inspect
# print(f"DEBUG: grib_processor.py is being loaded from: {inspect.getfile(sys.modules[__name__])}", file=sys.stderr)
# --- END REMOVE ---

def process_grib_parameter_extraction(
    grib_copy_path: str,
    input_grib_files_info: List[Tuple[str, str]], # List of (input_full_path, temp_output_filename) tuples
    temp_output_dir: str,
    final_output_filepath: str,
    grib_parameter_filter: str, # e.g., "shortName=2t"
    delete_temp_files: bool = True,
    logger: Optional[logging.Logger] = None # <--- THIS IS THE CRUCIAL ADDITION!
):

    # Use the provided logger, or fall back to the module's logger
    log = logger if logger is not None else module_logger

    log.info(f"Starting GRIB parameter extraction and merging for filter: '{grib_parameter_filter}'")

    # Ensure temporary output directory exists
    os.makedirs(temp_output_dir, exist_ok=True)
    log.debug(f"Ensured temporary GRIB output directory exists: {temp_output_dir}")

    temp_extracted_files = []

    # Step 1: Extract parameter from each input GRIB file
    for input_full_path, temp_output_filename in input_grib_files_info:
        temp_output_full_path = os.path.join(temp_output_dir, temp_output_filename)
     ## use operation system to combien path 
        command = [grib_copy_path, "-w", grib_parameter_filter, input_full_path, temp_output_full_path]
        log.info(f"Extracting '{grib_parameter_filter}' from '{os.path.basename(input_full_path)}' to '{os.path.basename(temp_output_full_path)}'.")

        try:
            execute_command(command) # Use pytap's execute_command
            temp_extracted_files.append(temp_output_full_path)
            log.debug(f"Successfully extracted to: {temp_output_full_path}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            log.error(f"Failed to extract parameter from '{input_full_path}'. Error: {e}")
            raise # For critical errors, it's often best to stop

    if not temp_extracted_files:
        log.warning("No files were successfully extracted. Merging skipped.")
        return None

    # Step 2: Merge the extracted temporary GRIB files
    log.info(f"Merging {len(temp_extracted_files)} extracted GRIB files into '{final_output_filepath}'.")
    try:
        merge_binary_files(final_output_filepath, temp_extracted_files) # Use pytap's merge_binary_files
        log.info(f"Successfully merged all extracted files to: {final_output_filepath}")
    except IOError as e:
        log.error(f"Error merging extracted GRIB files: {e}")
        raise # Re-raise if merging fails

    # Step 3: Clean up temporary files (if requested)
    if delete_temp_files:
        log.info("Deleting temporary extracted GRIB files.")
        delete_files(temp_extracted_files) # Use pytap's delete_files
        log.info("Temporary GRIB files deleted.")
    else:
        log.info("Skipping deletion of temporary GRIB files as requested.")

    log.info("GRIB processing completed successfully.")
    return final_output_filepath



def open_epygram_grib_resource(file_path: Path, logger_instance: logging.Logger = None):
    """
    Opens an epygram GRIB resource from a given file path.
    Based on the simple opening logic from the old script.

    Args:
        file_path (Path): The path to the GRIB file.
        logger_instance (logging.Logger, optional): Logger instance for messages.
                                                  If None, uses module_logger.

    Returns:
        epygram.formats.resource: The opened epygram GRIB resource.

    Raises:
        FileNotFoundError: If the GRIB file does not exist.
        Exception: For any other errors during file opening.
    """
    file_path = Path(file_path) # Ensure it's a Path object
    log = logger_instance if logger_instance is not None else module_logger
    log.debug(f"Attempting to open GRIB file resource for path: {file_path}")
    try:
        # Core logic from old script: epygram.formats.resource(f"tmp/2t_{AA_today}{MM_today}{DD_today}.grib", "r")
        arp = epygram.formats.resource(str(file_path), "r") # epygram expects a string path
        log.info(f"GRIB file '{file_path.name}' opened successfully.")
        return arp
    except FileNotFoundError:
        log.critical(f"GRIB file not found: {file_path}. Please ensure the file exists.")
        raise # Re-raise to be caught by the calling script
    except Exception as e:
        log.critical(f"Error opening GRIB file {file_path}: {e}")
        log.exception("Full traceback for GRIB file opening error:") # Log traceback
        raise # Re-raise to be caught by the calling script



def extract_field_for_stations(
    epygram_resource: Any, # epygram resource object
    stations_df: pd.DataFrame,
    field_short_name: str, # e.g., '2t'
    time_steps: List[int], # e.g., list(range(24, 49))
    kelvin_offset: float = 272.15, # Use 272.15 as per old code's logic
    logger_instance: logging.Logger = None,
    output_column_prefix: str = None
) -> Tuple[Dict[str, List[float]], List[List[float]]]:
    """
    Extracts a specified GRIB field for a list of stations across given time steps.
    This function directly encapsulates the explicit loop logic from the old script.

    Args:
        epygram_resource: The opened epygram GRIB resource.
        stations_df (pd.DataFrame): DataFrame with 'lon', 'lat', 'station' columns.
        field_short_name (str): The short name of the GRIB field to extract (e.g., '2t').
        time_steps (List[int]): A list of time steps (e.g., [24, 25, ..., 48]).
        kelvin_offset (float): The offset to use for Kelvin to Celsius conversion.
                               Defaults to 272.15 as explicitly used in the old script.
        logger_instance (logging.Logger, optional): Logger instance for messages.
                                                  If None, uses module_logger.
        output_column_prefix (str, optional): Prefix for output column names (e.g., 't2m').
                                              If None, field_short_name is used.

    Returns:
        Tuple[Dict[str, List[float]], List[List[float]]]:
            - extracted_data_dict: A dictionary where keys are column names (e.g., 't2m_24')
                                   and values are lists of extracted temperatures for each station.
            - all_times_data_for_minmax: A list of lists, where each inner list contains
                                         temperatures for a single time step across all stations.
                                         This corresponds to `t2m_all_times` from the old script.
    """
    log = logger_instance if logger_instance is not None else module_logger
    log.info(f"Starting extraction of field '{field_short_name}' for {len(stations_df)} stations "
             f"across {len(time_steps)} time steps using old script's explicit loop logic.")
    log.debug(f"Time steps to process: {time_steps}")
    log.debug(f"Kelvin offset for conversion: {kelvin_offset}")

    extracted_data_dict = {}
    all_times_data_for_minmax = [] # Corresponds to t2m_all_times in old script

    if output_column_prefix is None:
        output_column_prefix = field_short_name
        log.debug(f"No output column prefix provided, using field short name: '{output_column_prefix}'")
    else:
        log.debug(f"Using output column prefix: '{output_column_prefix}'")

    for time_step in time_steps:
        log.debug(f"Processing time step: {time_step}")
        try:
            # Core logic from old script: fld = arp.readfield({'shortName': '2t', 'stepRange': time})
            fld = epygram_resource.readfield({'shortName': field_short_name, 'stepRange': time_step})
            log.debug(f"Successfully read field '{field_short_name}' for step {time_step}.")
        except Exception as e:
            log.error(f"Failed to read field '{field_short_name}' for time step {time_step}: {e}. "
                      "Skipping this time step and populating with NaNs for all stations.")
            log.exception(f"Traceback for field read error at step {time_step}:")
            # Populate with NaNs for this time step if field reading fails
            extracted_data_dict[f'{output_column_prefix}_{time_step}'] = [np.nan] * len(stations_df)
            all_times_data_for_minmax.append([np.nan] * len(stations_df))
            continue # Move to the next time step

        values_for_current_timestep = []
        for index, row in stations_df.iterrows():
            station_name = row.get('station', f"SID_{row.get('SID', index)}") # Use 'station' or 'SID' or index for logging
            try:
                # Core logic from old script: t2m = fld.extract_point(row['lon'], row['lat']).data - 272.15
                extracted_value = fld.extract_point(row['lon'], row['lat']).data - kelvin_offset
                values_for_current_timestep.append(extracted_value)
                log.debug(f"Extracted {extracted_value:.2f} (C) for station '{station_name}' at lon={row['lon']:.2f}, lat={row['lat']:.2f}, step {time_step}.")
            except Exception as point_e:
                log.warning(f"Could not extract point for station '{station_name}' (lon={row['lon']:.2f}, lat={row['lat']:.2f}) "
                            f"at time step {time_step}: {point_e}. Appending NaN.")
                log.debug(f"Traceback for point extraction warning for station '{station_name}' at step {time_step}:", exc_info=True)
                values_for_current_timestep.append(np.nan)

        extracted_data_dict[f'{output_column_prefix}_{time_step}'] = values_for_current_timestep
        all_times_data_for_minmax.append(values_for_current_timestep)

    log.info("Finished GRIB data extraction for all specified time steps and stations.")
    return extracted_data_dict, all_times_data_for_minmax


def read_and_process_bufr_temperature(
    bufr_file_path: Union[str, Path],
    target_column_name: str,
    bufr_src_column: str = "airTemperature",
    logger_instance: Optional[logging.Logger] = None
) -> Optional[pd.DataFrame]:
    """
    Reads temperature data from a BUFR file using a specified BUFR key (defaults to 'airTemperature'),
    converts to Celsius, drops duplicates by station, and renames the temperature column.

    Args:
        bufr_file_path (Union[str, Path]): Path to the BUFR file.
        target_column_name (str): The desired name for the processed temperature column (e.g., 'tmin', 'tmax', 't2m_06').
        bufr_src_column (str, optional): The specific BUFR descriptor name to read.
                                         Defaults to 'airTemperature'. This allows flexibility for Tmin/Tmax.
        logger_instance (Optional[logging.Logger]): An optional module_logger instance to use for messages.
                                                    If None, a default module_logger is used.

    Returns:
        Optional[pd.DataFrame]: A Pandas DataFrame with 'stationOrSiteName' and the processed temperature column,
                                or None if the file cannot be processed or no data is found.
    """
    file_path = Path(bufr_file_path).resolve()
    # Use provided module_logger or create a minimal one for the function if none is provided
    current_logger = logger_instance if logger_instance is not None else logging.getLogger(__name__)

    current_logger.info(f"Processing BUFR file: {file_path} for key '{bufr_src_column}'")
    try:
        df = pdbufr.read_bufr(
            file_path,
            columns=("stationOrSiteName", bufr_src_column)
        )
        current_logger.debug(f"Successfully read {len(df)} records from {file_path}.")

        if df.empty:
            current_logger.warning(f"No data records found in {file_path} for '{bufr_src_column}' after initial read.")
            return None

        # Convert temperature from Kelvin to Celsius
        df[bufr_src_column] = df[bufr_src_column] - 273.15
        
        # Ensure unique station entries per hour before merging
        df = df.drop_duplicates(subset=["stationOrSiteName"])
        current_logger.debug(f"Processed and cleaned data. Unique stations after dropping duplicates: {len(df)}")

        # Rename the source temperature column to the target name
        df = df.rename(columns={bufr_src_column: target_column_name})

        # Select and return only the necessary columns
        return df[["stationOrSiteName", target_column_name]]

    except KeyError as e:
        current_logger.error(f"Missing expected BUFR key '{bufr_src_column}' in data from {file_path}: {e}. Check BUFR file structure or 'bufr_src_column' parameter.", exc_info=True)
        return None
    except Exception as e:
        current_logger.error(f"An unexpected error occurred while processing {file_path} with key '{bufr_src_column}': {e}", exc_info=True)
        return None
