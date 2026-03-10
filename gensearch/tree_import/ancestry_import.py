"""Ancestry-specific tree import helpers.

Primary workflow: user exports GEDCOM from Ancestry, we import it and
tag people with their Ancestry tree/person IDs for linking back.
"""

import re
from typing import Optional

from gensearch.models import FamilyTree, Person
from gensearch.tree_import.gedcom_parser import GedcomParser
from gensearch.providers.ancestry import AncestryProvider


_ancestry = AncestryProvider()


def import_ancestry_gedcom(filepath: str, tree_id: Optional[str] = None) -> FamilyTree:
    """Import an Ancestry-exported GEDCOM and tag people with Ancestry IDs.

    Ancestry GEDCOM files often include custom tags like:
        1 _APID 1,1234::5678  (Ancestry Person ID reference)

    Args:
        filepath: Path to the .ged file exported from Ancestry
        tree_id: Your Ancestry tree ID (from the URL when viewing your tree)

    Returns:
        A FamilyTree with Ancestry metadata attached
    """
    parser = GedcomParser()
    tree = parser.parse_file(filepath)

    if tree_id:
        # Tag all people with the tree ID so we can build links back
        for person in tree.members.values():
            person.ancestry_tree_id = tree_id
            # Use the GEDCOM xref as a fallback person ID
            # Real Ancestry person IDs can be extracted from _APID tags
            person.ancestry_person_id = person.id

    # Second pass: try to extract _APID tags from the raw file
    _extract_ancestry_ids(filepath, tree)

    tree.name = f"Ancestry Tree {tree_id}" if tree_id else "Ancestry Import"
    return tree


def _extract_ancestry_ids(filepath: str, tree: FamilyTree) -> None:
    """Extract Ancestry-specific _APID tags from the raw GEDCOM."""
    current_xref = None
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 2)
            level = int(parts[0])

            if level == 0 and len(parts) >= 3 and parts[2] == "INDI":
                current_xref = parts[1].strip("@")
            elif level == 1 and parts[1] == "_APID" and current_xref:
                # _APID format: 1,dbid::pid or similar
                apid = parts[2] if len(parts) > 2 else ""
                person = tree.get_person(current_xref)
                if person:
                    person.ancestry_person_id = apid


def generate_ancestry_links(tree: FamilyTree) -> dict:
    """Generate Ancestry URLs for every person in the tree that has Ancestry IDs.

    Returns:
        Dict mapping person_id -> {"facts": url, "hints": url}
    """
    links = {}
    for person in tree.members.values():
        if person.ancestry_tree_id and person.ancestry_person_id:
            links[person.id] = {
                "facts": _ancestry.build_tree_url(
                    person.ancestry_tree_id, person.ancestry_person_id
                ),
                "hints": _ancestry.build_hints_url(
                    person.ancestry_tree_id, person.ancestry_person_id
                ),
                "name": person.full_name,
            }
    return links


def find_unreviewed_hints_candidates(tree: FamilyTree) -> list:
    """Find people in the tree who would most benefit from reviewing Ancestry hints.

    Prioritizes people with missing data.
    """
    candidates = []
    for person in tree.members.values():
        if not person.ancestry_tree_id:
            continue
        score = 0
        reasons = []
        if not person.birth_year:
            score += 2
            reasons.append("missing birth year")
        if not person.death_year:
            score += 1
            reasons.append("missing death year")
        if not person.birth_place:
            score += 1
            reasons.append("missing birth place")
        if not tree.get_parents(person.id):
            score += 3
            reasons.append("no parents (brick wall)")
        if not person.sources:
            score += 2
            reasons.append("no sources")
        if score > 0:
            candidates.append({
                "person": person,
                "score": score,
                "reasons": reasons,
                "hints_url": _ancestry.build_hints_url(
                    person.ancestry_tree_id, person.ancestry_person_id
                ),
            })
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates
