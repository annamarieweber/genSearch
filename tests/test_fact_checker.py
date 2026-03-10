"""Tests for the fact checker."""

import pytest
from gensearch.models import (
    Person, Relationship, FamilyTree, Event,
    Gender, RelationType,
)
from gensearch.fact_checker.checks import (
    check_biological_impossibilities,
    check_chronological_consistency,
    check_common_mistakes,
    check_duplicates,
    run_all_checks,
)


def test_death_before_birth():
    tree = FamilyTree("test")
    p = Person(id="1", first_name="John", last_name="Doe",
               birth_year=1900, death_year=1850)
    tree.add_person(p)
    issues = check_biological_impossibilities(tree)
    categories = [i.category for i in issues]
    assert "death_before_birth" in categories


def test_excessive_lifespan():
    tree = FamilyTree("test")
    p = Person(id="1", first_name="John", last_name="Doe",
               birth_year=1800, death_year=1950)
    tree.add_person(p)
    issues = check_biological_impossibilities(tree)
    categories = [i.category for i in issues]
    assert "excessive_lifespan" in categories


def test_mother_too_young():
    tree = FamilyTree("test")
    mother = Person(id="m", first_name="Jane", last_name="Doe",
                    gender=Gender.FEMALE, birth_year=1890)
    child = Person(id="c", first_name="Baby", last_name="Doe",
                   birth_year=1900)
    tree.add_person(mother)
    tree.add_person(child)
    tree.add_relationship(Relationship("c", "m", RelationType.PARENT))
    issues = check_biological_impossibilities(tree)
    categories = [i.category for i in issues]
    assert "mother_too_young" in categories


def test_parent_born_after_child():
    tree = FamilyTree("test")
    parent = Person(id="p", first_name="Dad", last_name="Doe",
                    gender=Gender.MALE, birth_year=1950)
    child = Person(id="c", first_name="Kid", last_name="Doe",
                   birth_year=1900)
    tree.add_person(parent)
    tree.add_person(child)
    tree.add_relationship(Relationship("c", "p", RelationType.PARENT))
    issues = check_biological_impossibilities(tree)
    categories = [i.category for i in issues]
    assert "parent_born_after_child" in categories


def test_anachronistic_place():
    tree = FamilyTree("test")
    p = Person(id="1", first_name="John", last_name="Doe",
               birth_year=1820, birth_place="Charleston, West Virginia, USA")
    tree.add_person(p)
    issues = check_common_mistakes(tree)
    categories = [i.category for i in issues]
    assert "anachronistic_place" in categories


def test_large_sibling_gap():
    tree = FamilyTree("test")
    parent = Person(id="p", first_name="Dad", last_name="Doe",
                    gender=Gender.MALE, birth_year=1850)
    c1 = Person(id="c1", first_name="Alice", last_name="Doe", birth_year=1875)
    c2 = Person(id="c2", first_name="Bob", last_name="Doe", birth_year=1900)
    tree.add_person(parent)
    tree.add_person(c1)
    tree.add_person(c2)
    tree.add_relationship(Relationship("c1", "p", RelationType.PARENT))
    tree.add_relationship(Relationship("c2", "p", RelationType.PARENT))
    issues = check_chronological_consistency(tree)
    categories = [i.category for i in issues]
    assert "large_sibling_gap" in categories


def test_duplicate_detection():
    tree = FamilyTree("test")
    p1 = Person(id="1", first_name="John", last_name="Smith", birth_year=1850)
    p2 = Person(id="2", first_name="John", last_name="Smith", birth_year=1851)
    tree.add_person(p1)
    tree.add_person(p2)
    issues = check_duplicates(tree)
    assert len(issues) > 0
    assert issues[0].category == "possible_duplicate"


def test_no_issues_for_clean_tree():
    tree = FamilyTree("test")
    father = Person(id="f", first_name="John", last_name="Smith",
                    gender=Gender.MALE, birth_year=1850, death_year=1920,
                    birth_place="Philadelphia, Pennsylvania, USA")
    child = Person(id="c", first_name="James", last_name="Smith",
                   gender=Gender.MALE, birth_year=1878, death_year=1945)
    tree.add_person(father)
    tree.add_person(child)
    tree.add_relationship(Relationship("c", "f", RelationType.PARENT))
    issues = check_biological_impossibilities(tree)
    # Should have no errors (age 28 at child's birth is normal)
    error_issues = [i for i in issues if i.severity.value == "error"]
    assert len(error_issues) == 0
