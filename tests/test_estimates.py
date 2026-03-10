"""Tests for the genealogy estimates engine."""

import pytest
from gensearch.estimates import (
    estimate_ancestor_birth_years,
    estimate_lifespan,
    suggest_migration_patterns,
    calculate_search_ranges,
)


def test_ancestor_estimates():
    results = estimate_ancestor_birth_years(1850, generations_back=3)
    assert len(results) == 3
    assert results[0]["label"] == "Parents"
    assert results[0]["estimated_birth_range"][0] < 1850
    assert results[0]["estimated_birth_range"][1] < 1850


def test_lifespan_estimate():
    result = estimate_lifespan(1850)
    assert result["estimated_death_range"][0] > 1850
    assert result["estimated_death_range"][1] > 1850
    assert result["life_expectancy_range"][0] >= 35


def test_migration_german_surname():
    results = suggest_migration_patterns("Schmidt", 1860)
    assert len(results) > 0
    origins = [r["origin"] for r in results]
    assert "Germany" in origins


def test_migration_italian_surname():
    results = suggest_migration_patterns("Rossini", 1900)
    assert len(results) > 0
    origins = [r["origin"] for r in results]
    assert "Italy" in origins


def test_search_ranges():
    ranges = calculate_search_ranges(1850)
    assert ranges["birth_records"] == (1848, 1852)
    assert ranges["marriage_records"] == (1868, 1885)
    assert 1850 in ranges["census_records_us"]
    assert 1860 in ranges["census_records_us"]


def test_search_ranges_with_death():
    ranges = calculate_search_ranges(1850, death_year=1920)
    assert ranges["death_records"] == (1919, 1921)
