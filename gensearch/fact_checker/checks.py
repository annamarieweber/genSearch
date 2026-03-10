"""Individual fact-check functions for genealogy trees."""

from typing import List, Set, Tuple

from gensearch.models import FamilyTree, Person, Gender
from gensearch.fact_checker.rules import (
    Issue, Severity,
    MIN_MOTHER_AGE, MAX_MOTHER_AGE, MIN_FATHER_AGE, MAX_FATHER_AGE,
    MAX_LIFESPAN, MIN_MARRIAGE_AGE, MAX_SIBLING_GAP,
    MAX_MONTHS_AFTER_FATHER_DEATH, TOO_PERFECT_YEAR_THRESHOLD,
    PLACE_DATE_CONSTRAINTS,
)


def run_all_checks(tree: FamilyTree) -> List[Issue]:
    """Run all fact checks on a tree and return all issues found."""
    issues = []
    issues.extend(check_biological_impossibilities(tree))
    issues.extend(check_chronological_consistency(tree))
    issues.extend(check_source_quality(tree))
    issues.extend(check_common_mistakes(tree))
    issues.extend(check_duplicates(tree))
    return issues


def check_biological_impossibilities(tree: FamilyTree) -> List[Issue]:
    """Check for biologically impossible facts."""
    issues = []

    for person in tree.members.values():
        # Death before birth
        if person.birth_year and person.death_year:
            if person.death_year < person.birth_year:
                issues.append(Issue(
                    severity=Severity.ERROR,
                    category="death_before_birth",
                    person_id=person.id,
                    person_name=person.full_name,
                    message=f"Death year ({person.death_year}) is before birth year ({person.birth_year})",
                ))

            # Excessive lifespan
            age = person.death_year - person.birth_year
            if age > MAX_LIFESPAN:
                issues.append(Issue(
                    severity=Severity.ERROR,
                    category="excessive_lifespan",
                    person_id=person.id,
                    person_name=person.full_name,
                    message=f"Lifespan of {age} years exceeds maximum ({MAX_LIFESPAN})",
                ))

        # Check parent-child age differences
        children = tree.get_children(person.id)
        for child in children:
            if not person.birth_year or not child.birth_year:
                continue

            age_at_birth = child.birth_year - person.birth_year

            if person.gender == Gender.FEMALE:
                if age_at_birth < MIN_MOTHER_AGE:
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category="mother_too_young",
                        person_id=person.id,
                        person_name=person.full_name,
                        message=f"Was {age_at_birth} at birth of {child.full_name} (minimum: {MIN_MOTHER_AGE})",
                    ))
                elif age_at_birth > MAX_MOTHER_AGE:
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category="mother_too_old",
                        person_id=person.id,
                        person_name=person.full_name,
                        message=f"Was {age_at_birth} at birth of {child.full_name} (maximum: {MAX_MOTHER_AGE})",
                    ))
            elif person.gender == Gender.MALE:
                if age_at_birth < MIN_FATHER_AGE:
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category="father_too_young",
                        person_id=person.id,
                        person_name=person.full_name,
                        message=f"Was {age_at_birth} at birth of {child.full_name} (minimum: {MIN_FATHER_AGE})",
                    ))
                elif age_at_birth > MAX_FATHER_AGE:
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category="father_too_old",
                        person_id=person.id,
                        person_name=person.full_name,
                        message=f"Was {age_at_birth} at birth of {child.full_name} (maximum: {MAX_FATHER_AGE})",
                    ))

            # Negative age (parent born after child)
            if age_at_birth < 0:
                issues.append(Issue(
                    severity=Severity.ERROR,
                    category="parent_born_after_child",
                    person_id=person.id,
                    person_name=person.full_name,
                    message=f"Born {abs(age_at_birth)} years AFTER child {child.full_name}",
                ))

        # Birth after parent's death
        if person.birth_year:
            parents = tree.get_parents(person.id)
            for parent in parents:
                if parent.death_year and person.birth_year > parent.death_year:
                    grace = 1 if parent.gender == Gender.MALE else 0
                    if person.birth_year > parent.death_year + grace:
                        issues.append(Issue(
                            severity=Severity.ERROR,
                            category="born_after_parent_death",
                            person_id=person.id,
                            person_name=person.full_name,
                            message=(
                                f"Born in {person.birth_year}, but {parent.gender.value} parent "
                                f"{parent.full_name} died in {parent.death_year}"
                            ),
                        ))

    return issues


def check_chronological_consistency(tree: FamilyTree) -> List[Issue]:
    """Check for chronological inconsistencies."""
    issues = []

    for person in tree.members.values():
        # Event ordering: birth < marriage < death
        birth = person.birth_year
        death = person.death_year

        marriage_events = [e for e in person.events if e.event_type == "marriage"]
        for marriage in marriage_events:
            if marriage.year:
                if birth and marriage.year < birth:
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category="marriage_before_birth",
                        person_id=person.id,
                        person_name=person.full_name,
                        message=f"Marriage ({marriage.year}) before birth ({birth})",
                    ))
                if death and marriage.year > death:
                    issues.append(Issue(
                        severity=Severity.ERROR,
                        category="marriage_after_death",
                        person_id=person.id,
                        person_name=person.full_name,
                        message=f"Marriage ({marriage.year}) after death ({death})",
                    ))
                if birth:
                    age_at_marriage = marriage.year - birth
                    if age_at_marriage < MIN_MARRIAGE_AGE:
                        issues.append(Issue(
                            severity=Severity.WARNING,
                            category="young_marriage",
                            person_id=person.id,
                            person_name=person.full_name,
                            message=f"Married at age {age_at_marriage} (minimum: {MIN_MARRIAGE_AGE})",
                        ))

        # Sibling gap check
        children = tree.get_children(person.id)
        children_with_years = sorted(
            [(c, c.birth_year) for c in children if c.birth_year],
            key=lambda x: x[1],
        )
        for i in range(1, len(children_with_years)):
            prev_child, prev_year = children_with_years[i - 1]
            curr_child, curr_year = children_with_years[i]
            gap = curr_year - prev_year
            if gap > MAX_SIBLING_GAP:
                issues.append(Issue(
                    severity=Severity.WARNING,
                    category="large_sibling_gap",
                    person_id=person.id,
                    person_name=person.full_name,
                    message=(
                        f"{gap}-year gap between children {prev_child.full_name} ({prev_year}) "
                        f"and {curr_child.full_name} ({curr_year}) — possible missing child"
                    ),
                ))

    return issues


def check_source_quality(tree: FamilyTree) -> List[Issue]:
    """Check source quality across the tree."""
    issues = []

    for person in tree.members.values():
        if not person.sources:
            issues.append(Issue(
                severity=Severity.WARNING,
                category="no_sources",
                person_id=person.id,
                person_name=person.full_name,
                message="No sources attached — facts are unverified",
            ))
        else:
            # Check if all sources are user trees (unreliable)
            from gensearch.models import SourceType
            all_tree_sources = all(
                s.source_type == SourceType.USER_TREE for s in person.sources
            )
            if all_tree_sources:
                issues.append(Issue(
                    severity=Severity.WARNING,
                    category="tree_only_sources",
                    person_id=person.id,
                    person_name=person.full_name,
                    message="Only source is another user's tree — consider finding primary sources",
                ))

    return issues


def check_common_mistakes(tree: FamilyTree) -> List[Issue]:
    """Check for common genealogy data-entry mistakes."""
    issues = []

    for person in tree.members.values():
        # Wrong century check — parent born after child
        parents = tree.get_parents(person.id)
        for parent in parents:
            if parent.birth_year and person.birth_year:
                if parent.birth_year > person.birth_year:
                    # Check if off by exactly 100 years
                    diff = parent.birth_year - person.birth_year
                    if 90 <= diff <= 110 or -110 <= diff <= -90:
                        issues.append(Issue(
                            severity=Severity.ERROR,
                            category="wrong_century",
                            person_id=parent.id,
                            person_name=parent.full_name,
                            message=(
                                f"Birth year {parent.birth_year} may be off by 100 years "
                                f"(child {person.full_name} born {person.birth_year})"
                            ),
                        ))

        # Impossible locations — place names that didn't exist yet
        if person.birth_year and person.birth_place:
            for place_name, earliest_year in PLACE_DATE_CONSTRAINTS.items():
                if place_name.lower() in person.birth_place.lower():
                    if person.birth_year < earliest_year:
                        issues.append(Issue(
                            severity=Severity.WARNING,
                            category="anachronistic_place",
                            person_id=person.id,
                            person_name=person.full_name,
                            message=(
                                f"Birth place '{person.birth_place}' uses '{place_name}' "
                                f"but that name didn't exist until {earliest_year} "
                                f"(birth year: {person.birth_year})"
                            ),
                        ))

        # Too-perfect data — exact dates going way back
        if person.birth_year and person.birth_year < TOO_PERFECT_YEAR_THRESHOLD:
            birth_event = person.birth_event
            if birth_event and birth_event.date:
                # If the date has day precision (not just a year)
                import re
                if re.search(r'\d{1,2}\s+\w+\s+\d{4}', birth_event.date or ""):
                    issues.append(Issue(
                        severity=Severity.WARNING,
                        category="too_perfect_data",
                        person_id=person.id,
                        person_name=person.full_name,
                        message=(
                            f"Exact birth date '{birth_event.date}' before {TOO_PERFECT_YEAR_THRESHOLD} "
                            f"is suspicious — civil registration didn't exist in most places"
                        ),
                    ))

    return issues


def check_duplicates(tree: FamilyTree) -> List[Issue]:
    """Detect likely duplicate people that should be merged."""
    issues = []
    seen: Set[Tuple[str, str, int]] = set()
    people_list = list(tree.members.values())

    for i, p1 in enumerate(people_list):
        for p2 in people_list[i + 1:]:
            # Same name check (case-insensitive)
            if (p1.first_name.lower() == p2.first_name.lower() and
                    p1.last_name.lower() == p2.last_name.lower()):
                # Similar dates
                if p1.birth_year and p2.birth_year:
                    year_diff = abs(p1.birth_year - p2.birth_year)
                    if year_diff <= 2:
                        pair = tuple(sorted([p1.id, p2.id]))
                        if pair not in seen:
                            seen.add(pair)
                            issues.append(Issue(
                                severity=Severity.SUGGESTION,
                                category="possible_duplicate",
                                person_id=p1.id,
                                person_name=p1.full_name,
                                message=(
                                    f"Possible duplicate: {p1.full_name} (b. {p1.birth_year}) "
                                    f"and {p2.full_name} (b. {p2.birth_year}) [ID: {p2.id}]"
                                ),
                            ))
                elif p1.birth_year is None and p2.birth_year is None:
                    # Both have no birth year — still might be duplicates
                    pair = tuple(sorted([p1.id, p2.id]))
                    if pair not in seen:
                        seen.add(pair)
                        issues.append(Issue(
                            severity=Severity.SUGGESTION,
                            category="possible_duplicate",
                            person_id=p1.id,
                            person_name=p1.full_name,
                            message=(
                                f"Possible duplicate: {p1.full_name} and {p2.full_name} "
                                f"(same name, no dates to compare) [ID: {p2.id}]"
                            ),
                        ))

    return issues
