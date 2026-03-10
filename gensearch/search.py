"""Search orchestrator — multi-person and family-aware search."""

import csv
import json
from typing import Dict, List, Optional

from gensearch.models import FamilyTree, Person
from gensearch.estimates import calculate_search_ranges, estimate_lifespan
from gensearch.utils import census_years_for_lifespan
from gensearch.providers.ancestry import AncestryProvider
from gensearch.providers.familysearch import FamilySearchProvider
from gensearch.providers.findmypast import FindMyPastProvider
from gensearch.providers.findagrave import FindAGraveProvider
from gensearch.providers.billiongraves import BillionGravesProvider

ALL_PROVIDERS = {
    "ancestry": AncestryProvider(),
    "findmypast": FindMyPastProvider(),
    "familysearch": FamilySearchProvider(),
    "findagrave": FindAGraveProvider(),
    "billiongraves": BillionGravesProvider(),
}


def search_person(
    first: str, last: str, place: str = "", year: str = "",
    sites: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Generate search URLs for a single person across all providers."""
    providers = {k: ALL_PROVIDERS[k] for k in (sites or ALL_PROVIDERS.keys())}
    return {name: p.build_url(first, last, place, year) for name, p in providers.items()}


def search_relatives(
    person: Person,
    tree: Optional[FamilyTree] = None,
    sites: Optional[List[str]] = None,
) -> Dict[str, List[Dict]]:
    """Auto-generate searches for likely relatives of a person.

    Uses known data or estimates to search for parents, siblings, spouse, children.
    """
    results = {"parents": [], "siblings": [], "spouse": [], "children": []}
    birth_year = person.estimated_birth_year
    place = person.birth_place or ""

    if not birth_year:
        return results

    # Parents: same last name, same place, ~25 years earlier
    parent_year = str(birth_year - 27)
    results["parents"].append({
        "description": f"Father of {person.full_name}",
        "search": {"last": person.last_name, "place": place, "year": parent_year},
        "urls": search_person("", person.last_name, place, parent_year, sites),
    })

    # Siblings: same last name, same place, similar year
    for offset in [-5, -3, -1, 1, 3, 5]:
        sib_year = str(birth_year + offset)
        results["siblings"].append({
            "description": f"Sibling of {person.full_name} (b. ~{sib_year})",
            "search": {"last": person.last_name, "place": place, "year": sib_year},
            "urls": search_person("", person.last_name, place, sib_year, sites),
        })

    # Children: same last name, same place, 25-35 years later
    for offset in [25, 30, 35]:
        child_year = str(birth_year + offset)
        results["children"].append({
            "description": f"Child of {person.full_name} (b. ~{child_year})",
            "search": {"last": person.last_name, "place": place, "year": child_year},
            "urls": search_person("", person.last_name, place, child_year, sites),
        })

    return results


def search_from_tree(
    tree: FamilyTree,
    sites: Optional[List[str]] = None,
) -> List[Dict]:
    """Generate targeted searches for people in a tree with missing data.

    Focuses on brick walls and people missing key facts.
    """
    results = []
    missing = tree.get_people_missing_data()
    brick_walls = tree.get_brick_walls()

    # Priority 1: Brick wall ancestors
    for person in brick_walls:
        place = person.birth_place or person.death_place or ""
        year = str(person.estimated_birth_year) if person.estimated_birth_year else ""
        urls = search_person(person.first_name, person.last_name, place, year, sites)

        parent_searches = search_relatives(person, tree, sites) if person.estimated_birth_year else {}

        results.append({
            "person": person.full_name,
            "person_id": person.id,
            "priority": "high",
            "reason": "brick wall — no parents known",
            "direct_search": urls,
            "relative_searches": parent_searches.get("parents", []),
        })

    # Priority 2: People missing birth year
    for person in missing.get("no_birth_year", []):
        if person.id in {p.id for p in brick_walls}:
            continue  # already covered
        place = person.birth_place or person.death_place or ""
        urls = search_person(person.first_name, person.last_name, place, "", sites)
        results.append({
            "person": person.full_name,
            "person_id": person.id,
            "priority": "medium",
            "reason": "missing birth year",
            "direct_search": urls,
        })

    return results


def batch_search_from_csv(filepath: str, sites: Optional[List[str]] = None) -> List[Dict]:
    """Run searches for multiple people from a CSV file.

    Expected CSV columns: first_name, last_name, place, year
    """
    results = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            first = row.get("first_name", "").strip()
            last = row.get("last_name", "").strip()
            place = row.get("place", "").strip()
            year = row.get("year", "").strip()
            if first and last:
                urls = search_person(first, last, place, year, sites)
                results.append({
                    "person": f"{first} {last}",
                    "search_params": {"first": first, "last": last, "place": place, "year": year},
                    "urls": urls,
                })
    return results


def batch_search_from_json(filepath: str, sites: Optional[List[str]] = None) -> List[Dict]:
    """Run searches for multiple people from a JSON file.

    Expected format: [{"first_name": "...", "last_name": "...", "place": "...", "year": "..."}]
    """
    with open(filepath, "r") as f:
        people = json.load(f)

    results = []
    for person_data in people:
        first = person_data.get("first_name", "").strip()
        last = person_data.get("last_name", "").strip()
        place = person_data.get("place", "").strip()
        year = str(person_data.get("year", "")).strip()
        if first and last:
            urls = search_person(first, last, place, year, sites)
            results.append({
                "person": f"{first} {last}",
                "search_params": person_data,
                "urls": urls,
            })
    return results


def generate_census_searches(
    person: Person,
    country: str = "US",
    sites: Optional[List[str]] = None,
) -> List[Dict]:
    """Generate census-year-specific searches for a person."""
    birth_year = person.estimated_birth_year
    if not birth_year:
        return []

    death_year = person.estimated_death_year
    years = census_years_for_lifespan(birth_year, death_year, country)
    place = person.birth_place or ""

    results = []
    for census_year in years:
        age = census_year - birth_year
        urls = search_person(
            person.first_name, person.last_name, place, str(census_year), sites
        )
        results.append({
            "census_year": census_year,
            "estimated_age": age,
            "urls": urls,
        })
    return results
