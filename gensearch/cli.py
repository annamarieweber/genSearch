"""CLI entry point for genSearch — full-featured genealogy tool."""

import argparse
import json
import sys
import webbrowser

from gensearch.search import (
    search_person, search_from_tree, batch_search_from_csv,
    batch_search_from_json, generate_census_searches, search_relatives,
)
from gensearch.tree_import.gedcom_parser import GedcomParser, export_gedcom
from gensearch.tree_import.ancestry_import import (
    import_ancestry_gedcom, generate_ancestry_links, find_unreviewed_hints_candidates,
)
from gensearch.estimates import (
    analyze_person_estimates, analyze_tree_estimates,
    estimate_ancestor_birth_years, suggest_migration_patterns,
)
from gensearch.fact_checker.report import generate_report
from gensearch.models import Person


def main():
    parser = argparse.ArgumentParser(
        prog="gensearch",
        description="GenSearch — Multi-site genealogy search, tree analysis, and fact checking.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- search ---
    sp_search = subparsers.add_parser("search", help="Search for a person across genealogy sites")
    sp_search.add_argument("--first", required=True, help="First name")
    sp_search.add_argument("--last", required=True, help="Last name")
    sp_search.add_argument("--place", default="", help="Place (city, state, country)")
    sp_search.add_argument("--year", default="", help="Birth year")
    sp_search.add_argument("--sites", nargs="+", help="Sites to search")
    sp_search.add_argument("--json", dest="as_json", action="store_true")
    sp_search.add_argument("--no-open", action="store_true", help="Don't open browser")

    # --- estimate ---
    sp_est = subparsers.add_parser("estimate", help="Generate genealogy estimates for a person")
    sp_est.add_argument("--first", required=True)
    sp_est.add_argument("--last", required=True)
    sp_est.add_argument("--year", required=True, type=int, help="Birth year")
    sp_est.add_argument("--generations", type=int, default=4, help="Generations to estimate back")

    # --- import ---
    sp_import = subparsers.add_parser("import", help="Import a GEDCOM file")
    sp_import.add_argument("file", help="Path to .ged file")
    sp_import.add_argument("--tree-id", help="Ancestry tree ID (from URL)")
    sp_import.add_argument("--check", action="store_true", help="Run fact checker after import")
    sp_import.add_argument("--report-format", choices=["text", "json", "html"], default="text")

    # --- check ---
    sp_check = subparsers.add_parser("check", help="Fact-check a GEDCOM tree file")
    sp_check.add_argument("file", help="Path to .ged file")
    sp_check.add_argument("--root", help="Root person ID for completeness analysis")
    sp_check.add_argument("--format", choices=["text", "json", "html"], default="text")
    sp_check.add_argument("--output", help="Output file path (default: stdout)")

    # --- batch ---
    sp_batch = subparsers.add_parser("batch", help="Batch search from CSV or JSON")
    sp_batch.add_argument("file", help="Path to CSV or JSON file")
    sp_batch.add_argument("--sites", nargs="+", help="Sites to search")

    # --- migration ---
    sp_mig = subparsers.add_parser("migration", help="Suggest migration patterns for a surname")
    sp_mig.add_argument("--last", required=True, help="Last name")
    sp_mig.add_argument("--year", type=int, help="Approximate year")

    # --- hints ---
    sp_hints = subparsers.add_parser("hints", help="Find Ancestry hints to review from a GEDCOM")
    sp_hints.add_argument("file", help="Path to .ged file")
    sp_hints.add_argument("--tree-id", required=True, help="Ancestry tree ID")
    sp_hints.add_argument("--limit", type=int, default=20, help="Max results")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "search":
        _cmd_search(args)
    elif args.command == "estimate":
        _cmd_estimate(args)
    elif args.command == "import":
        _cmd_import(args)
    elif args.command == "check":
        _cmd_check(args)
    elif args.command == "batch":
        _cmd_batch(args)
    elif args.command == "migration":
        _cmd_migration(args)
    elif args.command == "hints":
        _cmd_hints(args)


def _cmd_search(args):
    urls = search_person(args.first, args.last, args.place, args.year, args.sites)
    if args.as_json:
        print(json.dumps(urls, indent=2))
    else:
        for name, url in urls.items():
            print(f"[{name}] {url}")
        if not args.no_open:
            for url in urls.values():
                webbrowser.open_new_tab(url)


def _cmd_estimate(args):
    person = Person(
        id="cli", first_name=args.first, last_name=args.last,
        birth_year=args.year,
    )
    result = analyze_person_estimates(person)

    print(f"\nEstimates for {person.full_name} (b. {args.year})")
    print("=" * 50)

    if "lifespan" in result:
        ls = result["lifespan"]
        print(f"\nEstimated death: {ls['estimated_death_range'][0]}-{ls['estimated_death_range'][1]}")

    if "ancestor_estimates" in result:
        print("\nAncestor birth year estimates:")
        for est in result["ancestor_estimates"][:args.generations]:
            r = est["estimated_birth_range"]
            print(f"  {est['label']}: ~{r[0]}-{r[1]} (est. {est['midpoint']})")

    if "search_ranges" in result:
        sr = result["search_ranges"]
        print(f"\nRecommended search ranges:")
        print(f"  Birth records: {sr['birth_records']}")
        print(f"  Marriage records: {sr['marriage_records']}")
        print(f"  Death records: {sr['death_records']}")
        print(f"  US Census years: {sr['census_records_us']}")
        print(f"  Military records: {sr['military_records']}")

    if "migration_suggestions" in result and result["migration_suggestions"]:
        print(f"\nMigration pattern suggestions:")
        for sug in result["migration_suggestions"]:
            print(f"  {sug['origin']}: {sug['context']}")
            print(f"    Likely ports: {', '.join(sug['likely_ports'])}")
            print(f"    Likely destinations: {', '.join(sug['likely_destinations'])}")


def _cmd_import(args):
    tree = import_ancestry_gedcom(args.file, args.tree_id) if args.tree_id else GedcomParser().parse_file(args.file)
    stats = tree.stats()
    print(f"Imported {stats['total_people']} people, {stats['total_relationships']} relationships")
    print(f"Brick walls: {stats['brick_walls']}")

    if args.check:
        report = generate_report(tree, format=args.report_format)
        print(f"\n{report}")


def _cmd_check(args):
    tree = GedcomParser().parse_file(args.file)
    report = generate_report(tree, root_person_id=args.root, format=args.format)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


def _cmd_batch(args):
    filepath = args.file
    if filepath.endswith(".csv"):
        results = batch_search_from_csv(filepath, args.sites)
    else:
        results = batch_search_from_json(filepath, args.sites)

    print(json.dumps(results, indent=2))


def _cmd_migration(args):
    suggestions = suggest_migration_patterns(args.last, args.year)
    if not suggestions:
        print(f"No migration pattern suggestions for surname '{args.last}'")
        return

    print(f"\nMigration pattern suggestions for '{args.last}':")
    for sug in suggestions:
        print(f"\n  {sug['origin']} ({sug['period'][0]}-{sug['period'][1]})")
        print(f"    {sug['context']}")
        print(f"    Likely ports: {', '.join(sug['likely_ports'])}")
        print(f"    Likely destinations: {', '.join(sug['likely_destinations'])}")
        for reason in sug["reasons"]:
            print(f"    * {reason}")


def _cmd_hints(args):
    tree = import_ancestry_gedcom(args.file, args.tree_id)
    candidates = find_unreviewed_hints_candidates(tree)

    print(f"\nTop {min(args.limit, len(candidates))} people to review hints for:\n")
    for c in candidates[:args.limit]:
        person = c["person"]
        print(f"  {person.full_name} (score: {c['score']})")
        print(f"    Reasons: {', '.join(c['reasons'])}")
        print(f"    Hints: {c['hints_url']}")
        print()


if __name__ == "__main__":
    main()
