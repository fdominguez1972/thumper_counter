"""
Seasonal analysis models and enums.
Feature: 008-rut-season-analysis
"""

from enum import Enum
from datetime import date
from typing import Tuple


class SeasonalFilter(Enum):
    """
    Predefined seasonal date ranges for Hopkins Ranch, Texas whitetail deer.

    All seasons use UTC timezone alignment with trail camera timestamps.
    """

    RUT_SEASON = {
        "name": "Rut Season",
        "description": "Whitetail deer breeding season (Sept 1 - Jan 31)",
        "start_month": 9,
        "start_day": 1,
        "end_month": 1,
        "end_day": 31,
        "crosses_year": True
    }

    SPRING = {
        "name": "Spring",
        "description": "Fawn birthing season (Mar 1 - May 31)",
        "start_month": 3,
        "start_day": 1,
        "end_month": 5,
        "end_day": 31,
        "crosses_year": False
    }

    SUMMER = {
        "name": "Summer",
        "description": "Antler growth period (Jun 1 - Aug 31)",
        "start_month": 6,
        "start_day": 1,
        "end_month": 8,
        "end_day": 31,
        "crosses_year": False
    }

    FALL = {
        "name": "Fall",
        "description": "Pre-rut and rut activity (Sept 1 - Nov 30)",
        "start_month": 9,
        "start_day": 1,
        "end_month": 11,
        "end_day": 30,
        "crosses_year": False
    }

    @staticmethod
    def get_date_range(season: "SeasonalFilter", year: int) -> Tuple[date, date]:
        """
        Convert seasonal filter to actual start/end dates for a given year.

        Args:
            season: SeasonalFilter enum value
            year: Target year (e.g., 2024)

        Returns:
            Tuple of (start_date, end_date)

        Example:
            >>> start, end = SeasonalFilter.get_date_range(SeasonalFilter.RUT_SEASON, 2024)
            >>> print(start, end)
            2024-09-01 2025-01-31
        """
        config = season.value
        start_date = date(year, config["start_month"], config["start_day"])

        if config["crosses_year"]:
            end_date = date(year + 1, config["end_month"], config["end_day"])
        else:
            end_date = date(year, config["end_month"], config["end_day"])

        return start_date, end_date
