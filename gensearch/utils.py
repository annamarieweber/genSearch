"""Utility functions for URL encoding, date math, and common helpers."""

from urllib.parse import quote_plus
from typing import List, Optional


def encode_place(place: str) -> str:
    """URL-encode a place string (e.g. 'Philadelphia, Pennsylvania, USA')."""
    return quote_plus(place)


def encode_name(name: str) -> str:
    """URL-encode a name."""
    return quote_plus(name)


# US Census years
US_CENSUS_YEARS = list(range(1790, 1960, 10))  # 1790-1950

# UK Census years
UK_CENSUS_YEARS = [1841, 1851, 1861, 1871, 1881, 1891, 1901, 1911, 1921]


def census_years_for_lifespan(
    birth_year: int,
    death_year: Optional[int] = None,
    country: str = "US",
) -> List[int]:
    """Return census years a person would appear in during their lifetime."""
    years = US_CENSUS_YEARS if country == "US" else UK_CENSUS_YEARS
    end = death_year or (birth_year + 85)
    return [y for y in years if birth_year <= y <= end]


def year_range_overlap(
    range1: tuple, range2: tuple
) -> bool:
    """Check if two year ranges overlap."""
    return range1[0] <= range2[1] and range2[0] <= range1[1]
