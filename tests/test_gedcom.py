"""Tests for GEDCOM import/export."""

import os
import tempfile
import pytest
from gensearch.tree_import.gedcom_parser import GedcomParser, export_gedcom
from gensearch.models import Gender


SAMPLE_GED = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample.ged")


def test_parse_sample():
    parser = GedcomParser()
    tree = parser.parse_file(SAMPLE_GED)
    assert len(tree.members) > 0
    # Sample has 8 people
    assert len(tree.members) == 8


def test_parse_names():
    parser = GedcomParser()
    tree = parser.parse_file(SAMPLE_GED)
    john = tree.get_person("I1")
    assert john is not None
    assert john.first_name == "John"
    assert john.last_name == "Smith"


def test_parse_dates():
    parser = GedcomParser()
    tree = parser.parse_file(SAMPLE_GED)
    john = tree.get_person("I1")
    assert john.birth_year == 1850
    assert john.death_year == 1920


def test_parse_places():
    parser = GedcomParser()
    tree = parser.parse_file(SAMPLE_GED)
    john = tree.get_person("I1")
    assert "Philadelphia" in john.birth_place


def test_parse_gender():
    parser = GedcomParser()
    tree = parser.parse_file(SAMPLE_GED)
    john = tree.get_person("I1")
    assert john.gender == Gender.MALE
    mary = tree.get_person("I2")
    assert mary.gender == Gender.FEMALE


def test_parse_relationships():
    parser = GedcomParser()
    tree = parser.parse_file(SAMPLE_GED)
    # John and Mary are parents of James and Elizabeth
    children = tree.get_children("I1")
    child_names = {c.first_name for c in children}
    assert "James" in child_names
    assert "Elizabeth" in child_names


def test_parse_spouses():
    parser = GedcomParser()
    tree = parser.parse_file(SAMPLE_GED)
    spouses = tree.get_spouses("I1")
    assert len(spouses) == 1
    assert spouses[0].first_name == "Mary"


def test_export_roundtrip():
    parser = GedcomParser()
    tree = parser.parse_file(SAMPLE_GED)

    with tempfile.NamedTemporaryFile(suffix=".ged", delete=False, mode="w") as f:
        tmppath = f.name

    try:
        export_gedcom(tree, tmppath)
        tree2 = GedcomParser().parse_file(tmppath)
        assert len(tree2.members) == len(tree.members)
    finally:
        os.unlink(tmppath)
