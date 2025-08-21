# src/pytaps/time_utils.py

from datetime import datetime, timedelta
from typing import Tuple, Literal, Optional, Union
import logging

logger = logging.getLogger(__name__)

def get_formatted_dates(
    date_to_process: Optional[datetime] = None,
    today_offset_days: int = 0,
    yesterday_offset_days: int = 1,
    date_format: str = '%Y%m%d',
    return_type: Literal['ymd_tuple', 'str_tuple'] = 'ymd_tuple'
) -> Union[Tuple[str, str, str, str, str, str], Tuple[str, str]]:
    """
    Prepares 'today's' and 'yesterday's' dates (or dates with an offset)
    in specified formats.

    Args:
        date_to_process (datetime, optional): The base datetime object to use for calculations.
                                              If None, `datetime.now()` is used.
        today_offset_days (int): Number of days to offset 'today' from `date_to_process`.
                                 (e.g., 0 for current day, 1 for tomorrow, -1 for yesterday).
        yesterday_offset_days (int): Number of days to offset 'yesterday' from the calculated 'today_dt'.
                                     (e.g., 1 for the day before 'today_dt').
        date_format (str): The format string for dates (e.g., '%Y%m%d', '%Y-%m-%d').
                           Only used if `return_type` is 'str_tuple'.
        return_type (Literal['ymd_tuple', 'str_tuple']):
            'ymd_tuple': Returns (YYYY_today, MM_today, DD_today, YYYY_yesterday, MM_yesterday, DD_yesterday).
            'str_tuple': Returns (formatted_today_str, formatted_yesterday_str) using `date_format`.

    Returns:
        Union[Tuple[str, str, str, str, str, str], Tuple[str, str]]:
            A tuple of formatted date strings based on `return_type`.

    Raises:
        ValueError: If an invalid `return_type` is specified.
    """
    if date_to_process is None:
        base_dt = datetime.now()
    else:
        base_dt = date_to_process

    today_dt = base_dt + timedelta(days=today_offset_days)
    yesterday_dt = today_dt - timedelta(days=yesterday_offset_days)

    logger.debug(f"Calculated dates - Base: {base_dt.strftime('%Y-%m-%d')}, Today: {today_dt.strftime('%Y-%m-%d')}, Yesterday: {yesterday_dt.strftime('%Y-%m-%d')}")

    if return_type == 'ymd_tuple':
        today_y, today_m, today_d = today_dt.strftime('%Y'), today_dt.strftime('%m'), today_dt.strftime('%d')
        yesterday_y, yesterday_m, yesterday_d = yesterday_dt.strftime('%Y'), yesterday_dt.strftime('%m'), yesterday_dt.strftime('%d')
        logger.debug(f"Returning YMD tuples: Today={today_y}-{today_m}-{today_d}, Yesterday={yesterday_y}-{yesterday_m}-{yesterday_d}")
        return today_y, today_m, today_d, yesterday_y, yesterday_m, yesterday_d
    elif return_type == 'str_tuple':
        formatted_today = today_dt.strftime(date_format)
        formatted_yesterday = yesterday_dt.strftime(date_format)
        logger.debug(f"Returning formatted strings ({date_format}): Today={formatted_today}, Yesterday={formatted_yesterday}")
        return formatted_today, formatted_yesterday
    else:
        raise ValueError(f"Invalid return_type: '{return_type}'. Must be 'ymd_tuple' or 'str_tuple'.")

