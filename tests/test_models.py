"""Tests for the data model."""

import pytest
from gensearch.models import (
    Person, Relationship, FamilyTree, Event,
    Gender, RelationType,
)


def _make_tree():
    tree = FamilyTree("Test Tree")

    grandpa = Person(id="gp", first_name="William", last_name="Smith",
                     gender=Gender.MALE, birth_year=1820)
    grandma = Person(id="gm", first_name="Sarah", last_name="Brown",
                     gender=Gender.FEMALE, birth_year=1825)
    father = Person(id="f", first_name="John", last_name="Smith",
                    gender=Gender.MALE, birth_year=1850, birth_place="Philadelphia, PA")
    mother = Person(id="m", first_name="Mary", last_name="Jones",
                    gender=Gender.FEMALE, birth_year=1855)
    child = Person(id="c", first_name="James", last_name="Smith",
                   gender=Gender.MALE, birth_year=1878)

    for p in [grandpa, grandma, father, mother, child]:
        tree.add_person(p)

    tree.add_relationship(Relationship("f", "gp", RelationType.PARENT))
    tree.add_relationship(Relationship("f", "gm", RelationType.PARENT))
    tree.add_relationship(Relationship("f", "m", RelationType.SPOUSE))
    tree.add_relationship(Relationship("c", "f", RelationType.PARENT))
    tree.add_relationship(Relationship("c", "m", RelationType.PARENT))

    return tree


def test_get_parents():
    tree = _make_tree()
    parents = tree.get_parents("f")
    assert len(parents) == 2
    names = {p.first_name for p in parents}
    assert "William" in names
    assert "Sarah" in names


def test_get_children():
    tree = _make_tree()
    children = tree.get_children("f")
    assert len(children) == 1
    assert children[0].first_name == "James"


def test_get_spouses():
    tree = _make_tree()
    spouses = tree.get_spouses("f")
    assert len(spouses) == 1
    assert spouses[0].first_name == "Mary"


def test_get_siblings():
    tree = _make_tree()
    siblings = tree.get_siblings("c")
    assert len(siblings) == 0  # only child


def test_get_ancestors():
    tree = _make_tree()
    ancestors = tree.get_ancestors("c", generations=2)
    names = {a.first_name for a in ancestors}
    assert "John" in names
    assert "Mary" in names
    assert "William" in names
    assert "Sarah" in names


def test_brick_walls():
    tree = _make_tree()
    walls = tree.get_brick_walls()
    # grandpa and grandma have children but no parents
    wall_names = {w.first_name for w in walls}
    assert "William" in wall_names
    assert "Sarah" in wall_names


def test_missing_data():
    tree = _make_tree()
    missing = tree.get_people_missing_data()
    # All people have birth years, none have sources
    assert len(missing["no_sources"]) == 5
    assert len(missing["no_birth_year"]) == 0
