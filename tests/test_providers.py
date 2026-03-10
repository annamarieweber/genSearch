"""Tests for search providers."""

import pytest
from gensearch.providers.ancestry import AncestryProvider
from gensearch.providers.familysearch import FamilySearchProvider
from gensearch.providers.findmypast import FindMyPastProvider
from gensearch.providers.findagrave import FindAGraveProvider
from gensearch.providers.billiongraves import BillionGravesProvider


def test_ancestry_url():
    p = AncestryProvider()
    url = p.build_url("John", "Smith", "Philadelphia, PA", "1850")
    assert "search.ancestry.com" in url
    assert "gsfn=John" in url
    assert "gsln=Smith" in url
    assert "msbdy=1850" in url


def test_familysearch_url():
    p = FamilySearchProvider()
    url = p.build_url("John", "Smith", "Philadelphia, PA", "1850")
    assert "familysearch.org" in url
    assert "givenname" in url
    assert "surname" in url


def test_findmypast_url():
    p = FindMyPastProvider()
    url = p.build_url("John", "Smith", "Philadelphia", "1850")
    assert "findmypast.com" in url
    assert "firstname=John" in url
    assert "lastname=Smith" in url


def test_findagrave_url():
    p = FindAGraveProvider()
    url = p.build_url("John", "Smith", "Philadelphia", "1850")
    assert "findagrave.com" in url
    assert "firstname=John" in url


def test_billiongraves_url():
    p = BillionGravesProvider()
    url = p.build_url("John", "Smith", "", "1850")
    assert "billiongraves.com" in url
    assert "given_names=John" in url


def test_ancestry_tree_urls():
    p = AncestryProvider()
    facts = p.build_tree_url("12345", "67890")
    assert "tree/12345/person/67890/facts" in facts
    hints = p.build_hints_url("12345", "67890")
    assert "tree/12345/person/67890/hints" in hints


def test_no_place_no_year():
    p = AncestryProvider()
    url = p.build_url("John", "Smith")
    assert "gsfn=John" in url
    assert "mswpn" not in url
    assert "msbdy" not in url
