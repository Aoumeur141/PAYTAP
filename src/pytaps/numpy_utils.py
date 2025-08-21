# pytaps/numpy_utils.py
import numpy as np
import logging
from typing import List, Tuple, Union, Optional


def calculate_nan_min_max(data: Union[List[List[float]], np.ndarray], logger_instance: logging.Logger = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculates the min and max values across multiple time steps for each entity,
    handling NaNs gracefully. This function directly replicates the min/max calculation
    logic from the old script (`np.array(data).T.min(axis=1)`).

    Args:
        data (Union[List[List[float]], np.ndarray]): Input data where inner lists/rows
                                                     represent values for a single time step
                                                     across all entities.
        logger_instance (logging.Logger, optional): Logger instance for messages.
                                                  If None, uses module_logger.

    Returns:
        Tuple[np.ndarray, np.ndarray]: A tuple containing two numpy arrays:
                                       (min_values_per_entity, max_values_per_entity).
                                       Returns arrays of NaNs if input is empty or an error occurs.
    """
    log = logger_instance if logger_instance is not None else module_logger
    log.info("Starting calculation of min/max values across time steps for each entity.")

    try:
        # Core logic from old script: t2m_all_times = np.array(t2m_all_times).T
        data_np = np.array(data, dtype=float) # Ensure float type to handle NaNs
        log.debug(f"Input data shape for min/max calculation: {data_np.shape}")

        if data_np.size == 0 or data_np.shape[0] == 0:
            log.warning("Input data for min/max calculation is empty. Returning arrays of NaNs.")
            # Determine the number of entities from the shape if possible, otherwise default to 0
            num_entities = data_np.shape[1] if data_np.ndim > 1 else 0
            return np.full(num_entities, np.nan), np.full(num_entities, np.nan)

        # Transpose the array so that entities are rows and time steps are columns.
        log.debug("Transposing data for min/max calculation (entities as rows, time steps as columns).")
        data_transposed = data_np.T
        log.debug(f"Transposed data shape: {data_transposed.shape}")

        # Core logic from old script: results['t2m_min'] = t2m_all_times.min(axis=1)
        # Use nanmin/nanmax to ignore NaNs when calculating min/max, which is safer.
        min_vals = np.nanmin(data_transposed, axis=1)
        max_vals = np.nanmax(data_transposed, axis=1)

        log.info("Min/Max temperatures calculated successfully.")
        log.debug(f"Sample min values (first 5): {min_vals[:5]}")
        log.debug(f"Sample max values (first 5): {max_vals[:5]}")
        return min_vals, max_vals
    except Exception as e:
        log.error(f"Error calculating min/max values: {e}. Populating min/max columns with NaNs.")
        log.exception("Full traceback for min/max calculation error:")
        # If an error occurs, try to determine the expected output shape for NaNs
        num_entities = 0
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            num_entities = len(data[0]) # Assuming data[0] represents first time step for all entities
        elif isinstance(data, np.ndarray) and data.ndim > 1:
            num_entities = data.shape[1]

        return np.full(num_entities, np.nan), np.full(num_entities, np.nan)

