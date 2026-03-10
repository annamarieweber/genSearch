"""Report generation for fact-check results."""

import json
from typing import List, Dict, Optional

from gensearch.models import FamilyTree
from gensearch.fact_checker.rules import Issue, Severity
from gensearch.fact_checker.checks import run_all_checks
from gensearch.fact_checker.completeness import analyze_completeness


def generate_report(
    tree: FamilyTree,
    root_person_id: Optional[str] = None,
    format: str = "text",
) -> str:
    """Generate a full fact-check report for a tree.

    Args:
        tree: The family tree to check
        root_person_id: Optional root person for completeness analysis
        format: "text", "json", or "html"

    Returns:
        Formatted report string
    """
    issues = run_all_checks(tree)

    completeness = None
    if root_person_id:
        completeness = analyze_completeness(tree, root_person_id)

    if format == "json":
        return _format_json(issues, completeness, tree)
    elif format == "html":
        return _format_html(issues, completeness, tree)
    else:
        return _format_text(issues, completeness, tree)


def _categorize_issues(issues: List[Issue]) -> Dict[str, List[Issue]]:
    """Group issues by severity."""
    categorized = {
        "errors": [i for i in issues if i.severity == Severity.ERROR],
        "warnings": [i for i in issues if i.severity == Severity.WARNING],
        "suggestions": [i for i in issues if i.severity == Severity.SUGGESTION],
    }
    return categorized


def _format_text(issues: List[Issue], completeness: Optional[Dict], tree: FamilyTree) -> str:
    """Format report as terminal text."""
    lines = []
    lines.append("=" * 70)
    lines.append("  GENEALOGY TREE FACT-CHECK REPORT")
    lines.append("=" * 70)
    lines.append("")

    stats = tree.stats()
    lines.append(f"Tree: {tree.name}")
    lines.append(f"People: {stats['total_people']}")
    lines.append(f"Relationships: {stats['total_relationships']}")
    lines.append(f"Brick walls: {stats['brick_walls']}")
    lines.append("")

    categorized = _categorize_issues(issues)

    # Errors
    lines.append(f"ERRORS ({len(categorized['errors'])})")
    lines.append("-" * 40)
    if categorized["errors"]:
        for issue in categorized["errors"]:
            lines.append(f"  [!] {issue.person_name}: {issue.message}")
            if issue.ancestry_url:
                lines.append(f"      Link: {issue.ancestry_url}")
    else:
        lines.append("  No errors found.")
    lines.append("")

    # Warnings
    lines.append(f"WARNINGS ({len(categorized['warnings'])})")
    lines.append("-" * 40)
    if categorized["warnings"]:
        for issue in categorized["warnings"]:
            lines.append(f"  [?] {issue.person_name}: {issue.message}")
    else:
        lines.append("  No warnings found.")
    lines.append("")

    # Suggestions
    lines.append(f"SUGGESTIONS ({len(categorized['suggestions'])})")
    lines.append("-" * 40)
    if categorized["suggestions"]:
        for issue in categorized["suggestions"]:
            lines.append(f"  [i] {issue.person_name}: {issue.message}")
    else:
        lines.append("  No suggestions.")
    lines.append("")

    # Completeness
    if completeness and "per_generation" in completeness:
        lines.append("TREE COMPLETENESS")
        lines.append("-" * 40)
        lines.append(f"  Overall: {completeness['overall_completeness_pct']}%")
        lines.append(f"  Total ancestors found: {completeness['total_ancestors_found']}/{completeness['total_ancestors_expected']}")
        lines.append("")
        for gen in completeness["per_generation"]:
            bar_len = int(gen["completeness_pct"] / 5)
            bar = "#" * bar_len + "." * (20 - bar_len)
            lines.append(f"  Gen {gen['generation']} ({gen['label']}): [{bar}] {gen['completeness_pct']}% ({gen['found']}/{gen['expected']})")
        lines.append("")

        if completeness.get("research_targets"):
            lines.append("TOP RESEARCH TARGETS")
            lines.append("-" * 40)
            for target in completeness["research_targets"][:10]:
                missing = ", ".join(target["missing_parents"])
                lines.append(f"  {target['person']} — missing {missing} (potential: {target['research_potential']})")
            lines.append("")

    lines.append("=" * 70)
    lines.append(f"Total issues: {len(issues)} ({len(categorized['errors'])} errors, "
                 f"{len(categorized['warnings'])} warnings, {len(categorized['suggestions'])} suggestions)")
    lines.append("=" * 70)

    return "\n".join(lines)


def _format_json(issues: List[Issue], completeness: Optional[Dict], tree: FamilyTree) -> str:
    """Format report as JSON."""
    categorized = _categorize_issues(issues)

    report = {
        "tree": {
            "name": tree.name,
            "stats": tree.stats(),
        },
        "issues": {
            "errors": [_issue_to_dict(i) for i in categorized["errors"]],
            "warnings": [_issue_to_dict(i) for i in categorized["warnings"]],
            "suggestions": [_issue_to_dict(i) for i in categorized["suggestions"]],
        },
        "totals": {
            "errors": len(categorized["errors"]),
            "warnings": len(categorized["warnings"]),
            "suggestions": len(categorized["suggestions"]),
            "total": len(issues),
        },
    }
    if completeness:
        report["completeness"] = completeness

    return json.dumps(report, indent=2, default=str)


def _format_html(issues: List[Issue], completeness: Optional[Dict], tree: FamilyTree) -> str:
    """Format report as HTML."""
    categorized = _categorize_issues(issues)
    stats = tree.stats()

    html = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='UTF-8'>",
        "<title>Tree Fact-Check Report</title>",
        "<style>",
        "body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }",
        "h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }",
        ".stats { background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0; }",
        ".error { color: #d32f2f; border-left: 4px solid #d32f2f; padding: 8px 12px; margin: 5px 0; background: #ffebee; }",
        ".warning { color: #f57c00; border-left: 4px solid #f57c00; padding: 8px 12px; margin: 5px 0; background: #fff3e0; }",
        ".suggestion { color: #1976d2; border-left: 4px solid #1976d2; padding: 8px 12px; margin: 5px 0; background: #e3f2fd; }",
        ".completeness-bar { background: #e0e0e0; border-radius: 4px; height: 20px; margin: 4px 0; }",
        ".completeness-fill { background: #4caf50; height: 100%; border-radius: 4px; }",
        "table { width: 100%; border-collapse: collapse; margin: 15px 0; }",
        "th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }",
        "th { background: #f5f5f5; }",
        "</style>",
        "</head><body>",
        "<h1>Genealogy Tree Fact-Check Report</h1>",
        f"<div class='stats'>",
        f"<strong>{tree.name}</strong> &mdash; {stats['total_people']} people, "
        f"{stats['total_relationships']} relationships, {stats['brick_walls']} brick walls",
        f"</div>",
    ]

    # Errors
    html.append(f"<h2>Errors ({len(categorized['errors'])})</h2>")
    for issue in categorized["errors"]:
        html.append(f"<div class='error'><strong>{issue.person_name}:</strong> {issue.message}</div>")

    # Warnings
    html.append(f"<h2>Warnings ({len(categorized['warnings'])})</h2>")
    for issue in categorized["warnings"]:
        html.append(f"<div class='warning'><strong>{issue.person_name}:</strong> {issue.message}</div>")

    # Suggestions
    html.append(f"<h2>Suggestions ({len(categorized['suggestions'])})</h2>")
    for issue in categorized["suggestions"]:
        html.append(f"<div class='suggestion'><strong>{issue.person_name}:</strong> {issue.message}</div>")

    # Completeness
    if completeness and "per_generation" in completeness:
        html.append("<h2>Tree Completeness</h2>")
        html.append(f"<p>Overall: <strong>{completeness['overall_completeness_pct']}%</strong></p>")
        html.append("<table><tr><th>Generation</th><th>Found</th><th>Expected</th><th>Completeness</th></tr>")
        for gen in completeness["per_generation"]:
            pct = gen["completeness_pct"]
            html.append(f"<tr><td>{gen['label']}</td><td>{gen['found']}</td><td>{gen['expected']}</td>")
            html.append(f"<td><div class='completeness-bar'><div class='completeness-fill' style='width:{pct}%'></div></div> {pct}%</td></tr>")
        html.append("</table>")

    html.append("</body></html>")
    return "\n".join(html)


def _issue_to_dict(issue: Issue) -> Dict:
    return {
        "severity": issue.severity.value,
        "category": issue.category,
        "person_id": issue.person_id,
        "person_name": issue.person_name,
        "message": issue.message,
        "details": issue.details,
        "ancestry_url": issue.ancestry_url,
    }
