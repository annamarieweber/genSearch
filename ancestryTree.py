#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ancestryTree.py - Access Ancestry public trees without a GEDCOM file

Three approaches:
  1. Search Ancestry's Public Member Trees (collection 1030) by name/place/date
  2. Direct link to a known person in a public tree using treeId + personId
  3. Search FamilySearch (free, open API with real tree data)

Usage:
  # Search public trees by name/place/year:
  python3 ancestryTree.py search "John" "Smith" "Pennsylvania" "1850"

  # Link directly to a known person in a public tree:
  python3 ancestryTree.py person <treeId> <personId>

  # Search FamilySearch open API:
  python3 ancestryTree.py familysearch "John" "Smith" "Pennsylvania" "1850"
"""

import sys
import webbrowser
from urllib.parse import urlencode, quote


# ---------------------------------------------------------------------------
# Approach 1: Search Ancestry Public Member Trees (no GEDCOM, no download)
# Collection 1030 = "Public Member Trees" on Ancestry
# ---------------------------------------------------------------------------

def search_public_trees(first_name, last_name, place="", year=""):
    """
    Generate a URL to search Ancestry's Public Member Trees (collection 1030).
    This searches across all public trees by name, place, and date — no GEDCOM needed.
    """
    params = {
        "name": f"{first_name} {last_name}".strip(),
        "name_x": "1",           # exact name match
    }
    if place:
        params["residence_place"] = place
    if year:
        params["birth_year"] = year
        params["birth_year_range"] = "5"

    base = "https://www.ancestry.com/search/collections/1030/"
    url = base + "?" + urlencode(params)
    return url


# ---------------------------------------------------------------------------
# Approach 2: Direct link to a person in a known public tree
# No GEDCOM download or export required — just treeId + personId from the URL
# ---------------------------------------------------------------------------

def build_tree_person_url(tree_id, person_id):
    """
    Build a direct URL to a person's profile in an Ancestry public tree.

    How to find treeId and personId:
      - Browse to any public tree on ancestry.com
      - The URL will look like:
          https://www.ancestry.com/family-tree/person/tree/12345678/person/987654321/facts
      - treeId  = 12345678
      - personId = 987654321

    This approach requires no GEDCOM file — just the two numeric IDs from the URL.
    """
    return f"https://www.ancestry.com/family-tree/person/tree/{tree_id}/person/{person_id}/facts"


def build_tree_home_url(tree_id):
    """Build a URL to the root/home view of a public tree."""
    return f"https://www.ancestry.com/family-tree/tree/{tree_id}/family"


# ---------------------------------------------------------------------------
# Approach 3: FamilySearch — free, fully documented public tree API
# No Ancestry account required. FamilySearch is the best open alternative.
# Docs: https://developers.familysearch.org/
# ---------------------------------------------------------------------------

def search_familysearch(first_name, last_name, place="", year=""):
    """
    Generate a URL to search FamilySearch's open genealogy records and tree.
    FamilySearch has a fully documented REST API — free and no GEDCOM needed.
    """
    query_parts = []
    if first_name:
        query_parts.append(f"+givenname:{quote(first_name)}")
    if last_name:
        query_parts.append(f"+surname:{quote(last_name)}")
    if place:
        query_parts.append(f"+residence_place:{quote(place)}~")
    if year:
        query_parts.append(f"+birth_year:{year}-{year}~")

    query = " ".join(query_parts)
    params = urlencode({"count": "20", "query": query})
    return f"https://familysearch.org/search/record/results?{params}"


def familysearch_tree_api_url(given_name, surname, birth_year="", birth_place=""):
    """
    Build a FamilySearch Family Tree API search URL.
    FamilySearch exposes a real REST API (no scraping needed):
      GET https://api.familysearch.org/platform/tree/search
    This returns GEDCOM X JSON — structured tree data without any GEDCOM file.

    Note: Requires a free FamilySearch account + access token for the API.
    The search UI URL below works without authentication.
    """
    params = {"givenName": given_name, "surname": surname}
    if birth_year:
        params["birthLikeYear"] = birth_year
    if birth_place:
        params["birthLikePlace"] = birth_place

    return "https://www.familysearch.org/search/tree/results?" + urlencode(params)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "search" and len(sys.argv) >= 4:
        first = sys.argv[2]
        last = sys.argv[3]
        place = sys.argv[4] if len(sys.argv) > 4 else ""
        year = sys.argv[5] if len(sys.argv) > 5 else ""

        url = search_public_trees(first, last, place, year)
        print(f"Ancestry Public Member Trees search:\n  {url}\n")
        webbrowser.open_new_tab(url)

    elif mode == "person" and len(sys.argv) == 4:
        tree_id = sys.argv[2]
        person_id = sys.argv[3]

        person_url = build_tree_person_url(tree_id, person_id)
        tree_url = build_tree_home_url(tree_id)
        print(f"Person profile:  {person_url}")
        print(f"Tree home view:  {tree_url}\n")
        webbrowser.open_new_tab(person_url)

    elif mode == "familysearch" and len(sys.argv) >= 4:
        first = sys.argv[2]
        last = sys.argv[3]
        place = sys.argv[4] if len(sys.argv) > 4 else ""
        year = sys.argv[5] if len(sys.argv) > 5 else ""

        records_url = search_familysearch(first, last, place, year)
        tree_url = familysearch_tree_api_url(first, last, year, place)
        print(f"FamilySearch records search:\n  {records_url}\n")
        print(f"FamilySearch tree search:\n  {tree_url}\n")
        webbrowser.open_new_tab(records_url)
        webbrowser.open_new_tab(tree_url)

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
