"""Configurable thresholds and rules for fact checking."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class Severity(Enum):
    ERROR = "error"        # Biological impossibilities, dates out of order
    WARNING = "warning"    # Missing sources, suspicious gaps
    SUGGESTION = "suggestion"  # Missing data, merge candidates


@dataclass
class Issue:
    """A single fact-check issue found in the tree."""
    severity: Severity
    category: str
    person_id: str
    person_name: str
    message: str
    details: Optional[str] = None
    ancestry_url: Optional[str] = None


# --- Configurable thresholds ---

# Age at childbirth
MIN_MOTHER_AGE = 13
MAX_MOTHER_AGE = 50
MIN_FATHER_AGE = 13
MAX_FATHER_AGE = 75

# Lifespan
MAX_LIFESPAN = 110

# Marriage
MIN_MARRIAGE_AGE = 14

# Sibling gaps
MAX_SIBLING_GAP = 20  # years between siblings that suggests a missing child

# Birth after parent death
MAX_MONTHS_AFTER_FATHER_DEATH = 9  # months (pregnancy)

# Location travel — days per distance threshold for historical periods
# If someone appears in two places closer together in time than plausible
# we flag it. Simplified: flag if <6 months apart and different countries.
MIN_TRAVEL_MONTHS_DIFFERENT_COUNTRY = 6

# Census age tolerance
CENSUS_AGE_TOLERANCE = 3  # years of allowed discrepancy

# Too-perfect data threshold
TOO_PERFECT_YEAR_THRESHOLD = 1650  # exact dates before this are suspicious

# Historical place names — places that didn't exist before certain dates
PLACE_DATE_CONSTRAINTS = {
    "West Virginia": 1863,
    "Oklahoma": 1907,
    "Arizona": 1912,
    "New Mexico": 1912,
    "Alaska": 1959,
    "Hawaii": 1959,
    "North Dakota": 1889,
    "South Dakota": 1889,
    "Montana": 1889,
    "Washington": 1889,
    "Idaho": 1890,
    "Wyoming": 1890,
    "Utah": 1896,
}
