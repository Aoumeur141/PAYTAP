# ~/Téléchargements/PyTAP-main/src/pytaps/grib_processor.py

import epygram
import numpy as np
import pandas as pd
import os
import logging

# Get a module-level logger. The main script will configure the handlers.
logger = logging.getLogger(__name__)

def process_arpege_grib_data(grib_file_path: str, stations_df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes an ARPEGE GRIB file to extract 2m temperature (2t) for specified stations
    across forecast steps 24h to 48h, and calculates min/max temperatures.

    Args:
        grib_file_path (str): Absolute path to the ARPEGE GRIB file.
        stations_df (pd.DataFrame): DataFrame containing station metadata
                                    with 'station', 'SID', 'lon', 'lat' columns.

    Returns:
        pd.DataFrame: A DataFrame with station metadata and extracted 2m temperatures
                      for each time step (t2m_24, t2m_25, ..., t2m_48),
                      plus 't2m_min' and 't2m_max' columns.

    Raises:
        FileNotFoundError: If the GRIB file does not exist.
        ValueError: If the stations_df is empty or missing required columns.
        Exception: For other errors during GRIB processing or data extraction.
    """
    if stations_df.empty:
        raise ValueError("Stations DataFrame is empty. Cannot process GRIB data without stations.")
    if not all(col in stations_df.columns for col in ['station', 'SID', 'lon', 'lat']):
        raise ValueError("Stations DataFrame must contain 'station', 'SID', 'lon', 'lat' columns.")

    arp = None # Initialize GRIB resource variable
    logger.info(f"Attempting to open GRIB file: {grib_file_path}")
    try:
        arp = epygram.formats.resource(grib_file_path, "r")
        logger.info("GRIB file opened successfully.")
    except FileNotFoundError:
        logger.error(f"GRIB file not found: {grib_file_path}.")
        raise FileNotFoundError(f"GRIB file not found: {grib_file_path}")
    except Exception as e:
        logger.error(f"Error opening GRIB file {grib_file_path}: {e}")
        raise Exception(f"Failed to open GRIB file: {e}")

    # Initialisation du dictionnaire pour stocker les valeurs de température
    results = {
        'station': stations_df['station'].tolist(),
        'SID': stations_df['SID'].tolist(),
        'lon': stations_df['lon'].tolist(),
        'lat': stations_df['lat'].tolist()
    }
    logger.info("Initialized results dictionary with station metadata (station, SID, lon, lat).")

    # List to store temperature values per station for min/max calculation
    t2m_all_times_raw = []
    logger.info("Starting extraction of 2m temperature data from GRIB file for each time step and station.")

    # Loop over time steps (from 24h to 48h inclusive)
    for time_step in range(24, 49, 1):
        try:
            logger.debug(f"Processing time step: {time_step}h.")
            # epygram uses 'stepRange' for forecast hour
            fld = arp.readfield({'shortName': '2t', 'stepRange': time_step})
            t2m_values_for_step = []

            # Extract data for each station
            for index, row in stations_df.iterrows():
                try:
                    # Conversion Kelvin -> Celsius (0°C = 273.15 K)
                    t2m = fld.extract_point(row['lon'], row['lat']).data - 273.15
                    t2m_values_for_step.append(t2m)
                    logger.debug(f"  Station {row['station']} (lon:{row['lon']}, lat:{row['lat']}) at step {time_step}h: {t2m:.2f} °C")
                except Exception as e:
                    logger.warning(f"  Could not extract point for station {row['station']} (lon:{row['lon']}, lat:{row['lat']}) at time step {time_step}h: {e}. Appending NaN.")
                    t2m_values_for_step.append(np.nan) # Append NaN if extraction fails for a station

            # Add values to the dictionary
            results[f't2m_{time_step}'] = t2m_values_for_step
            t2m_all_times_raw.append(t2m_values_for_step)
            logger.info(f"Successfully processed and stored data for time step {time_step}h. Extracted {len(t2m_values_for_step)} values.")
        except KeyError:
            logger.warning(f"Field '2t' with stepRange '{time_step}' not found in GRIB file. Skipping this time step and filling with NaNs.")
            # If a time step is missing, ensure the list of lists remains consistent
            t2m_all_times_raw.append([np.nan] * len(stations_df))
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing time step {time_step}h: {e}. Skipping this time step and filling with NaNs.")
            t2m_all_times_raw.append([np.nan] * len(stations_df))

    # Close the GRIB resource if it was opened
    if arp:
        try:
            arp.close()
            logger.info("GRIB file closed successfully.")
        except Exception as e:
            logger.error(f"Error closing GRIB file: {e}")

    # --- Calculation of Min/Max ---
    logger.info("Calculating min and max temperatures across all time steps for each station.")
    try:
        # Convert to numpy array and transpose to align with stations (rows=stations, cols=time_steps)
        t2m_all_times_np = np.array(t2m_all_times_raw)

        if t2m_all_times_np.size == 0 or t2m_all_times_np.shape[0] == 0:
            logger.error("No temperature data collected for min/max calculation. All min/max will be NaN.")
            results['t2m_min'] = [np.nan] * len(stations_df)
            results['t2m_max'] = [np.nan] * len(stations_df)
        else:
            t2m_all_times_transposed = t2m_all_times_np.T
            # Use nanmin/nanmax to correctly handle cases where some values are NaN
            results['t2m_min'] = np.nanmin(t2m_all_times_transposed, axis=1)
            results['t2m_max'] = np.nanmax(t2m_all_times_transposed, axis=1)
            logger.info("Min/Max temperatures calculated successfully.")
    except Exception as e:
        logger.error(f"Error calculating min/max temperatures: {e}. Populating min/max columns with NaNs.")
        results['t2m_min'] = [np.nan] * len(stations_df)
        results['t2m_max'] = [np.nan] * len(stations_df)

    # --- Conversion to DataFrame ---
    logger.info("Converting results dictionary to pandas DataFrame.")
    try:
        final_table = pd.DataFrame(results)
        logger.info("DataFrame created successfully.")
        logger.debug(f"Final table head:\n{final_table.head()}")
        return final_table
    except Exception as e:
        logger.error(f"Error creating final DataFrame: {e}")
        raise Exception(f"Failed to create final DataFrame: {e}")

