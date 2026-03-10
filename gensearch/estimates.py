"""Genealogy estimation engine.

Provides generational estimates, lifespan predictions, migration pattern
suggestions, and search year range calculations.
"""

from typing import Dict, List, Optional, Tuple
from gensearch.models import Person, FamilyTree
from gensearch.utils import census_years_for_lifespan


# --- Generational interval tables ---

GENERATION_INTERVALS = {
    # (start_year, end_year): (min_interval, max_interval)
    (0, 1700): (22, 25),
    (1700, 1850): (25, 28),
    (1850, 1950): (27, 32),
    (1950, 2100): (28, 35),
}


def _get_generation_interval(year: int) -> Tuple[int, int]:
    """Get the expected generational interval for a given era."""
    for (start, end), interval in GENERATION_INTERVALS.items():
        if start <= year < end:
            return interval
    return (25, 30)  # default


# --- Lifespan tables ---

LIFESPAN_BY_ERA = {
    (0, 1800): (35, 50),
    (1800, 1900): (40, 60),
    (1900, 1950): (55, 70),
    (1950, 2100): (70, 85),
}


def _get_lifespan_range(birth_year: int) -> Tuple[int, int]:
    """Estimated lifespan range based on birth year."""
    for (start, end), span in LIFESPAN_BY_ERA.items():
        if start <= birth_year < end:
            return span
    return (60, 80)


# --- Migration pattern data ---

MIGRATION_PATTERNS = [
    {
        "origin": "Ireland",
        "surname_hints": [],  # Irish surnames are too varied for simple matching
        "period": (1840, 1870),
        "ports": ["New York (Castle Garden/Ellis Island)", "Boston", "Philadelphia"],
        "destinations": ["New York", "Boston", "Philadelphia", "Chicago"],
        "context": "Irish Potato Famine immigration wave",
    },
    {
        "origin": "Germany",
        "surname_hints": ["berg", "stein", "mann", "burg", "wald", "bauer", "schmidt",
                          "schneider", "fischer", "weber", "meyer", "müller", "schulz",
                          "wagner", "becker", "hoffmann", "koch", "richter"],
        "period": (1830, 1890),
        "ports": ["Philadelphia", "Baltimore", "New York", "New Orleans"],
        "destinations": ["Pennsylvania", "Ohio", "Wisconsin", "Minnesota", "Missouri", "Texas"],
        "context": "German immigration wave (political upheaval + economic opportunity)",
    },
    {
        "origin": "Italy",
        "surname_hints": ["ini", "ino", "elli", "etti", "ucci", "acci", "one", "osi"],
        "period": (1880, 1920),
        "ports": ["New York (Ellis Island)"],
        "destinations": ["New York", "New Jersey", "Pennsylvania", "Massachusetts", "California"],
        "context": "Italian immigration wave (Southern Italy economic hardship)",
    },
    {
        "origin": "Eastern Europe",
        "surname_hints": ["ski", "sky", "wicz", "czyk", "enko", "ovich", "ovic"],
        "period": (1880, 1920),
        "ports": ["New York (Ellis Island)", "Baltimore"],
        "destinations": ["New York", "Chicago", "Cleveland", "Detroit", "Pittsburgh"],
        "context": "Eastern European immigration (pogroms, economic hardship)",
    },
    {
        "origin": "Scandinavia",
        "surname_hints": ["son", "sen", "strom", "lund", "berg", "gren", "qvist"],
        "period": (1850, 1910),
        "ports": ["New York", "Quebec"],
        "destinations": ["Minnesota", "Wisconsin", "Iowa", "North Dakota", "Nebraska"],
        "context": "Scandinavian immigration (land availability in Midwest)",
    },
    {
        "origin": "England/Scotland",
        "surname_hints": [],
        "period": (1607, 1850),
        "ports": ["Boston", "Philadelphia", "Jamestown", "Charleston"],
        "destinations": ["New England", "Virginia", "Pennsylvania", "Carolinas"],
        "context": "British colonial and post-colonial immigration",
    },
]


def estimate_ancestor_birth_years(
    known_birth_year: int,
    generations_back: int = 4,
) -> List[Dict]:
    """Estimate birth year ranges for ancestors going back N generations.

    Returns a list of dicts with generation number and estimated year range.
    """
    results = []
    current_year = known_birth_year

    for gen in range(1, generations_back + 1):
        interval = _get_generation_interval(current_year)
        min_year = current_year - interval[1]
        max_year = current_year - interval[0]
        mid_year = (min_year + max_year) // 2

        results.append({
            "generation": gen,
            "label": _generation_label(gen),
            "estimated_birth_range": (min_year, max_year),
            "midpoint": mid_year,
        })
        current_year = mid_year

    return results


def _generation_label(n: int) -> str:
    labels = {
        1: "Parents",
        2: "Grandparents",
        3: "Great-grandparents",
        4: "2x Great-grandparents",
        5: "3x Great-grandparents",
        6: "4x Great-grandparents",
    }
    if n in labels:
        return labels[n]
    return f"{n - 2}x Great-grandparents"


def estimate_lifespan(birth_year: int) -> Dict:
    """Estimate death year range and life expectancy for a person."""
    lifespan = _get_lifespan_range(birth_year)
    return {
        "birth_year": birth_year,
        "estimated_death_range": (birth_year + lifespan[0], birth_year + lifespan[1]),
        "life_expectancy_range": lifespan,
    }


def suggest_migration_patterns(last_name: str, year: Optional[int] = None) -> List[Dict]:
    """Suggest likely migration patterns based on surname and time period."""
    suggestions = []
    name_lower = last_name.lower()

    for pattern in MIGRATION_PATTERNS:
        score = 0
        reasons = []

        # Check surname hints
        for hint in pattern["surname_hints"]:
            if name_lower.endswith(hint) or hint in name_lower:
                score += 2
                reasons.append(f"surname ending '{hint}' suggests {pattern['origin']} origin")
                break

        # Check time period
        if year:
            period = pattern["period"]
            if period[0] <= year <= period[1]:
                score += 1
                reasons.append(f"year {year} falls within {pattern['origin']} immigration period ({period[0]}-{period[1]})")
            elif period[0] - 30 <= year <= period[1] + 30:
                score += 0.5
                reasons.append(f"year {year} is near {pattern['origin']} immigration period")

        if score > 0:
            suggestions.append({
                "origin": pattern["origin"],
                "score": score,
                "period": pattern["period"],
                "likely_ports": pattern["ports"],
                "likely_destinations": pattern["destinations"],
                "context": pattern["context"],
                "reasons": reasons,
            })

    suggestions.sort(key=lambda s: s["score"], reverse=True)
    return suggestions


def calculate_search_ranges(birth_year: int, death_year: Optional[int] = None) -> Dict:
    """Calculate useful year ranges for different record types."""
    lifespan = estimate_lifespan(birth_year)
    est_death = death_year or lifespan["estimated_death_range"][1]

    return {
        "birth_records": (birth_year - 2, birth_year + 2),
        "marriage_records": (birth_year + 18, birth_year + 35),
        "census_records_us": census_years_for_lifespan(birth_year, est_death, "US"),
        "census_records_uk": census_years_for_lifespan(birth_year, est_death, "UK"),
        "death_records": lifespan["estimated_death_range"] if not death_year else (death_year - 1, death_year + 1),
        "military_records": (birth_year + 18, birth_year + 45),
        "immigration_records": (birth_year + 15, birth_year + 40),
    }


def analyze_person_estimates(person: Person) -> Dict:
    """Generate all estimates for a single person."""
    result = {"person": person.full_name}

    birth_year = person.estimated_birth_year
    if not birth_year:
        result["error"] = "No birth year available for estimates"
        return result

    result["lifespan"] = estimate_lifespan(birth_year)
    result["ancestor_estimates"] = estimate_ancestor_birth_years(birth_year)
    result["search_ranges"] = calculate_search_ranges(birth_year, person.death_year)
    result["migration_suggestions"] = suggest_migration_patterns(
        person.last_name, birth_year
    )
    return result


def analyze_tree_estimates(tree: FamilyTree) -> Dict:
    """Generate estimates for an entire tree, focusing on gaps."""
    brick_walls = tree.get_brick_walls()
    missing = tree.get_people_missing_data()

    results = {
        "tree_stats": tree.stats(),
        "brick_wall_estimates": [],
        "research_priorities": [],
    }

    # Generate estimates for brick wall ancestors
    for person in brick_walls:
        est = analyze_person_estimates(person)
        est["priority"] = "high"
        est["reason"] = "brick wall ancestor — no parents known"
        results["brick_wall_estimates"].append(est)

    # Generate research priorities for people missing data
    for category, people in missing.items():
        for person in people[:10]:  # top 10 per category
            results["research_priorities"].append({
                "person": person.full_name,
                "person_id": person.id,
                "missing": category,
                "search_ranges": calculate_search_ranges(
                    person.estimated_birth_year
                ) if person.estimated_birth_year else None,
            })

    return results
