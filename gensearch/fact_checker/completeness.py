"""Tree completeness analysis — how complete is each generation?"""

from typing import Dict, List
from gensearch.models import FamilyTree, Person


def analyze_completeness(tree: FamilyTree, root_person_id: str, max_generations: int = 8) -> Dict:
    """Analyze tree completeness starting from a root person.

    For each generation, calculates how many of the expected ancestors
    are present and what percentage of the generation is filled in.

    Args:
        tree: The family tree to analyze
        root_person_id: ID of the person to start from
        max_generations: How many generations back to analyze

    Returns:
        Dict with per-generation stats and overall completeness
    """
    root = tree.get_person(root_person_id)
    if not root:
        return {"error": f"Person {root_person_id} not found"}

    generations = []
    current_gen = [root]

    for gen_num in range(1, max_generations + 1):
        expected = 2 ** gen_num  # 2 parents, 4 grandparents, 8 great-grandparents...
        next_gen = []

        for person in current_gen:
            parents = tree.get_parents(person.id)
            next_gen.extend(parents)

        found = len(next_gen)
        percentage = (found / expected * 100) if expected > 0 else 0

        # Categorize quality of data for found ancestors
        with_birth = sum(1 for p in next_gen if p.birth_year)
        with_death = sum(1 for p in next_gen if p.death_year)
        with_place = sum(1 for p in next_gen if p.birth_place)
        with_sources = sum(1 for p in next_gen if p.sources)

        generations.append({
            "generation": gen_num,
            "label": _gen_label(gen_num),
            "expected": expected,
            "found": found,
            "completeness_pct": round(percentage, 1),
            "with_birth_year": with_birth,
            "with_death_year": with_death,
            "with_birth_place": with_place,
            "with_sources": with_sources,
            "missing_count": expected - found,
            "people": [p.full_name for p in next_gen],
        })

        if not next_gen:
            break  # no point continuing if we've run out of ancestors

        current_gen = next_gen

    # Overall stats
    total_expected = sum(g["expected"] for g in generations)
    total_found = sum(g["found"] for g in generations)

    # Find the weakest branch (generation with lowest completeness)
    weakest = min(generations, key=lambda g: g["completeness_pct"]) if generations else None

    # Find the most promising research targets
    research_targets = _find_research_targets(tree, generations)

    return {
        "root_person": root.full_name,
        "generations_analyzed": len(generations),
        "total_ancestors_expected": total_expected,
        "total_ancestors_found": total_found,
        "overall_completeness_pct": round(total_found / total_expected * 100, 1) if total_expected else 0,
        "per_generation": generations,
        "weakest_generation": weakest,
        "research_targets": research_targets,
    }


def _find_research_targets(tree: FamilyTree, generations: List[Dict]) -> List[Dict]:
    """Identify the best research targets — people whose parents are missing."""
    targets = []

    for gen_data in generations:
        for person_name in gen_data["people"]:
            # Find the actual person object
            person = None
            for p in tree.members.values():
                if p.full_name == person_name:
                    person = p
                    break
            if not person:
                continue

            parents = tree.get_parents(person.id)
            if len(parents) < 2:
                missing_parent_type = []
                has_father = any(p.gender.value == "male" for p in parents)
                has_mother = any(p.gender.value == "female" for p in parents)
                if not has_father:
                    missing_parent_type.append("father")
                if not has_mother:
                    missing_parent_type.append("mother")

                targets.append({
                    "person": person.full_name,
                    "person_id": person.id,
                    "generation": gen_data["generation"],
                    "missing_parents": missing_parent_type,
                    "has_birth_year": person.birth_year is not None,
                    "has_birth_place": person.birth_place is not None,
                    "research_potential": "high" if person.birth_year and person.birth_place else
                                         "medium" if person.birth_year or person.birth_place else "low",
                })

    targets.sort(key=lambda t: {"high": 0, "medium": 1, "low": 2}[t["research_potential"]])
    return targets


def _gen_label(n: int) -> str:
    labels = {
        1: "Parents",
        2: "Grandparents",
        3: "Great-grandparents",
        4: "2x Great-grandparents",
        5: "3x Great-grandparents",
        6: "4x Great-grandparents",
        7: "5x Great-grandparents",
        8: "6x Great-grandparents",
    }
    return labels.get(n, f"{n - 2}x Great-grandparents")
