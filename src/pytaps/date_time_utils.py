# pytaps/date_utils.py

from datetime import datetime, timedelta
import logging
from typing import Tuple, Optional, Union

# Configure a module-level logger. This is good practice for reusable modules.
# The handler and formatter should be configured by the main application's setup_logger.
logger = logging.getLogger(__name__)

def get_ymd_for_today_and_yesterday(
    today_offset_days: int = 0,
    yesterday_offset_days: int = 0,
    logger_instance: Optional[logging.Logger] = None
) -> Tuple[str, str, str, str, str, str]:
    """
    Calculates and returns the year, month, and day strings for 'today' and 'yesterday',
    with optional offsets.

    Args:
        today_offset_days (int): Number of days to offset 'today' from the actual current date.
                                 (e.g., -1 for yesterday, 1 for tomorrow). Default is 0 (actual today).
        yesterday_offset_days (int): Number of days to offset 'yesterday' from the actual current date.
                                     (e.g., -1 for two days ago, 0 for yesterday). Default is 0 (actual yesterday).
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.
                                                     If None, the module's default logger is used.

    Returns:
        Tuple[str, str, str, str, str, str]: A tuple containing:
            (today_year, today_month, today_day, yesterday_year, yesterday_month, yesterday_day)
            All values are zero-padded strings (e.g., '2023', '01', '05').
    """
    current_logger = logger_instance if logger_instance is not None else logger
    current_logger.debug(f"Calculating YMD for 'today' (offset: {today_offset_days}) and 'yesterday' (offset: {yesterday_offset_days}).")

    actual_now = datetime.now()
    
    # Calculate 'today' based on offset
    today = actual_now + timedelta(days=today_offset_days)
    
    # Calculate 'yesterday' based on offset from actual_now (or from 'today' if that's the intent)
    # For simplicity and clarity, let's assume yesterday_offset_days applies to the actual yesterday.
    # If the user means "the day before 'today_offset_days'", they can pass today_offset_days - 1
    # For the original script's logic, today_offset_days=0 and yesterday_offset_days=0 works.
    yesterday = actual_now - timedelta(days=1) + timedelta(days=yesterday_offset_days)


    today_year = today.strftime('%Y')
    today_month = today.strftime('%m')
    today_day = today.strftime('%d')
    
    yesterday_year = yesterday.strftime('%Y')
    yesterday_month = yesterday.strftime('%m')
    yesterday_day = yesterday.strftime('%d')

    current_logger.info(f"Processed dates - Today: {today_year}-{today_month}-{today_day}, Yesterday: {yesterday_year}-{yesterday_month}-{yesterday_day}")
    
    return today_year, today_month, today_day, \
           yesterday_year, yesterday_month, yesterday_day

def get_current_datetime(
    format_string: Optional[str] = None,
    logger_instance: Optional[logging.Logger] = None
) -> Union[str, datetime]:
    """
    Returns the current datetime object or a formatted string representation.

    Args:
        format_string (Optional[str]): If provided, the datetime object will be formatted
                                       into this string format (e.g., '%Y-%m-%d %H:%M:%S').
                                       If None, the datetime object itself is returned.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.

    Returns:
        Union[str, datetime]: The current datetime object or its formatted string.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    now = datetime.now()
    if format_string:
        formatted_now = now.strftime(format_string)
        current_logger.debug(f"Current datetime formatted as: {formatted_now}")
        return formatted_now
    current_logger.debug(f"Current datetime object: {now}")
    return now

def get_date_n_days_ago_or_future(
    n_days: int,
    start_date: Optional[datetime] = None,
    format_string: Optional[str] = None,
    logger_instance: Optional[logging.Logger] = None
) -> Union[str, datetime]:
    """
    Calculates a date N days from a given start date (or current date if not provided).

    Args:
        n_days (int): The number of days to add or subtract. Positive for future, negative for past.
        start_date (Optional[datetime]): The starting datetime object. Defaults to current datetime.
        format_string (Optional[str]): If provided, the resulting datetime object will be formatted
                                       into this string format. If None, the datetime object is returned.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.

    Returns:
        Union[str, datetime]: The calculated datetime object or its formatted string.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    base_date = start_date if start_date is not None else datetime.now()
    
    result_date = base_date + timedelta(days=n_days)
    
    current_logger.debug(f"Calculated date {n_days} days from {base_date} is {result_date}.")

    if format_string:
        formatted_result = result_date.strftime(format_string)
        current_logger.debug(f"Formatted result: {formatted_result}")
        return formatted_result
    return result_date

def format_datetime_object(
    dt_obj: datetime,
    format_string: str,
    logger_instance: Optional[logging.Logger] = None
) -> str:
    """
    Formats a given datetime object into a string according to the specified format.

    Args:
        dt_obj (datetime): The datetime object to format.
        format_string (str): The format string (e.g., '%Y-%m-%d %H:%M:%S').
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.

    Returns:
        str: The formatted datetime string.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    formatted_str = dt_obj.strftime(format_string)
    current_logger.debug(f"Formatted datetime {dt_obj} to '{formatted_str}' using format '{format_string}'.")
    return formatted_str

def parse_date_string(
    date_str: str,
    format_string: str,
    logger_instance: Optional[logging.Logger] = None
) -> datetime:
    """
    Parses a date string into a datetime object according to the specified format.

    Args:
        date_str (str): The date string to parse.
        format_string (str): The format string (e.g., '%Y-%m-%d %H:%M:%S') that matches date_str.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.

    Returns:
        datetime: The parsed datetime object.
    
    Raises:
        ValueError: If the date_str does not match the format_string.
    """
    current_logger = logger_instance if logger_instance is not None else logger
    try:
        parsed_dt = datetime.strptime(date_str, format_string)
        current_logger.debug(f"Parsed date string '{date_str}' to datetime object {parsed_dt} using format '{format_string}'.")
        return parsed_dt
    except ValueError as e:
        current_logger.error(f"Failed to parse date string '{date_str}' with format '{format_string}': {e}")
        raise

def get_date_parts(
    dt_obj: datetime,
    logger_instance: Optional[logging.Logger] = None
) -> Tuple[str, str, str]:
    """
    Extracts year, month, and day as zero-padded strings from a datetime object.

    Args:
        dt_obj (datetime): The datetime object.
        logger_instance (Optional[logging.Logger]): An optional logger instance to use.

    Returns:
        Tuple[str, str, str]: (year_str, month_str, day_str)
    """
    current_logger = logger_instance if logger_instance is not None else logger
    year = dt_obj.strftime('%Y')
    month = dt_obj.strftime('%m')
    day = dt_obj.strftime('%d')
    current_logger.debug(f"Extracted date parts from {dt_obj}: Year={year}, Month={month}, Day={day}")
    return year, month, day

