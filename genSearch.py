#!/usr/bin/env python3
"""
                   _______                       __
.-----.-----.-----|   _   .-----.---.-.----.----|  |--.
|  _  |  -__|     |   1___|  -__|  _  |   _|  __|     |
|___  |_____|__|__|____   |_____|___._|__| |____|__|__|
|_____|           |:  1   |
                  |::.. . |
                  `-------'

GenSearch - Multi-site genealogy search tool.

Usage:
    python genSearch.py --first John --last Smith --place "Philadelphia, PA" --year 1850
    python genSearch.py John Smith "Philadelphia, PA" 1850
    python genSearch.py --first John --last Smith --place "Philadelphia, PA" --year 1850 --json
    python genSearch.py --first John --last Smith --place "Philadelphia, PA" --year 1850 --sites ancestry familysearch
"""

import argparse
import json
import sys
import webbrowser

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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Search multiple genealogy sites for a person."
    )
    parser.add_argument("first", nargs="?", help="First name (positional)")
    parser.add_argument("last", nargs="?", help="Last name (positional)")
    parser.add_argument("place", nargs="?", help="Place (positional)")
    parser.add_argument("year", nargs="?", help="Year (positional)")

    parser.add_argument("--first", dest="first_flag", help="First name")
    parser.add_argument("--last", dest="last_flag", help="Last name")
    parser.add_argument("--place", dest="place_flag", help="Place (city, state, country)")
    parser.add_argument("--year", dest="year_flag", help="Year (birth or approximate)")

    parser.add_argument(
        "--sites", nargs="+", choices=list(ALL_PROVIDERS.keys()),
        help="Which sites to search (default: all)",
    )
    parser.add_argument(
        "--json", dest="output_json", action="store_true",
        help="Output URLs as JSON instead of opening browser tabs",
    )
    parser.add_argument(
        "--no-open", dest="no_open", action="store_true",
        help="Print URLs but don't open browser tabs",
    )

    args = parser.parse_args(argv)

    # Merge positional and flag arguments (flags take priority)
    first = args.first_flag or args.first
    last = args.last_flag or args.last
    place = args.place_flag or args.place
    year = args.year_flag or args.year

    if not all([first, last]):
        parser.error("First name and last name are required.")

    return first, last, place or "", year or "", args


def main(argv=None):
    first, last, place, year, args = parse_args(argv)

    sites = args.sites or list(ALL_PROVIDERS.keys())
    providers = {name: ALL_PROVIDERS[name] for name in sites}

    urls = {}
    for name, provider in providers.items():
        urls[name] = provider.build_url(first, last, place, year)

    if args.output_json:
        print(json.dumps(urls, indent=2))
        return

    for name, url in urls.items():
        print(f"[{name}] {url}")

    if not args.no_open:
        for url in urls.values():
            webbrowser.open_new_tab(url)


if __name__ == "__main__":
    main()
