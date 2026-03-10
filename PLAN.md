# GenSearch Enhancement Plan: Family Tree Search & Genealogy Estimates

## Current State

The project is a Python 2.x CLI tool (`genSearch.py`) that takes a person's **first name, last name, place, and year** and opens browser tabs with pre-built search URLs for:
- **Ancestry.com**
- **FindMyPast.com**

There are stub HTML/JS files for a planned web UI. The script has some bugs (duplicate query parameters being appended) and uses Python 2 syntax.

---

## Plan Overview

Modernize the tool and extend it to support **family tree construction**, **genealogy estimates** (estimated birth/death ranges, likely family relationships, generational timelines), **Ancestry tree import**, and **automated fact-checking** to catch errors and inconsistencies in existing trees.

---

## Phase 1: Modernize & Fix the Core (`genSearch.py`)

### 1.1 Port to Python 3
- Replace `print sys.argv` with `print(sys.argv)`
- Replace `raw_input()` references (in comments) with `input()`
- Use `urllib.parse.quote_plus` for proper URL encoding instead of manual string replacement
- Add `argparse` for proper CLI argument parsing with `--first`, `--last`, `--place`, `--year` flags

### 1.2 Fix existing bugs
- Remove duplicate query parameter appends (lines 55-56 duplicate lines 40-41; lines 78-86 duplicate lines 42-51)
- Fix the FindMyPast encoding (`utf002c` should be `%2C` or handled properly)

### 1.3 Add structured output
- Instead of only opening browser tabs, also print the generated URLs to stdout
- Add a `--json` flag to output structured JSON with the search URLs (for use by other modules)

---

## Phase 2: Expand Search Sources

### 2.1 Add FamilySearch.org support
- The script already has a commented-out FamilySearch URL pattern (line 94)
- Implement FamilySearch query builder:
  - `https://www.familysearch.org/search/record/results?` with params: `givenname`, `surname`, `birth_place`, `birth_year`
- FamilySearch is free and has the largest genealogical database

### 2.2 Add FindAGrave.com support
- Search for burial/death records
- URL pattern: `https://www.findagrave.com/memorial/search?firstname=X&lastname=Y&location=Z`
- Useful for death date estimates and family plot discovery (family members often buried nearby)

### 2.3 Add BillionGraves.com support
- Complementary to FindAGrave for burial records
- Provides GPS coordinates for grave locations

### 2.4 Create a pluggable search provider architecture
- Define a `SearchProvider` base class with:
  - `name` property
  - `build_url(first, last, place, year)` method
  - `parse_results(html)` method (for future scraping)
- Each site becomes a provider module in a `providers/` directory

---

## Phase 3: Family Tree Data Model

### 3.1 Define a Person model
```python
class Person:
    first_name: str
    last_name: str
    birth_year: Optional[int]       # exact or estimated
    birth_year_range: Tuple[int, int]  # estimated range
    death_year: Optional[int]
    death_year_range: Tuple[int, int]
    birth_place: Optional[str]
    death_place: Optional[str]
    gender: Optional[str]
    relationships: List[Relationship]
```

### 3.2 Define a Relationship model
```python
class Relationship:
    person: Person
    relation_type: str  # "parent", "child", "spouse", "sibling"
```

### 3.3 Define a FamilyTree model
```python
class FamilyTree:
    root_person: Person
    members: Dict[str, Person]

    def add_person(...)
    def add_relationship(...)
    def get_ancestors(person, generations=4)
    def get_descendants(person, generations=4)
    def export_gedcom()  # standard genealogy format
```

### 3.4 GEDCOM import/export
- Support importing `.ged` (GEDCOM) files - the standard genealogy file format
- Support exporting the tree to GEDCOM for use in other tools
- Use or adapt an existing Python GEDCOM library

---

## Phase 4: Genealogy Estimates Engine

### 4.1 Generational estimator
- Given one known person with a birth year, estimate ancestor/descendant birth years
- Use configurable generational intervals:
  - Default: ~25-30 years per generation
  - Adjustable by era (earlier centuries had younger parents)
  - Historical averages:
    - Pre-1700: ~22-25 years/generation
    - 1700-1850: ~25-28 years/generation
    - 1850-1950: ~27-32 years/generation
    - Post-1950: ~28-35 years/generation

### 4.2 Lifespan estimator
- Estimate death year range based on birth year and historical life expectancy data:
  - Pre-1800: ~35-50 years average (high infant mortality skews this)
  - 1800-1900: ~40-60 years
  - 1900-1950: ~55-70 years
  - Post-1950: ~70-85 years
- Adjust by region/country if place data is available

### 4.3 Migration pattern suggestions
- Based on last name origin and time period, suggest likely migration paths
- Example: German surnames + 1850s = likely immigration through Philadelphia or Baltimore
- Build a simple rules-based lookup for common patterns:
  - Irish immigration waves (1840s-1860s)
  - German immigration (1830s-1890s)
  - Italian immigration (1880s-1920s)
  - Eastern European (1880s-1920s)

### 4.4 Search year range calculator
- When searching for a person, automatically calculate useful year ranges to search:
  - Birth records: birth_year ± 2
  - Marriage records: birth_year + 18 to birth_year + 35
  - Census records: every 10 years during estimated lifespan
  - Death records: estimated death year range
  - Military records: birth_year + 18 to birth_year + 45

---

## Phase 5: Ancestry Tree Integration

### 5.1 GEDCOM export from Ancestry
- Ancestry allows exporting your tree as a GEDCOM (.ged) file
- Add a guided workflow: instructions + CLI command to import the exported file
- Parse the GEDCOM into the internal `FamilyTree` model (Phase 3)

### 5.2 Ancestry API / Web scraping (if available)
- Ancestry has had unofficial/partner APIs over the years
- Investigate current options:
  - **RootsMagic / TreeShare protocol** — used by desktop software to sync with Ancestry trees
  - **Ancestry HTML scraping** — parse tree pages if the user provides session cookies (authenticated scraping of their own data)
  - **ThruLines data** — Ancestry's own relationship estimation feature; extract suggested connections
- Fallback: provide deep-link URLs directly into the user's Ancestry tree for specific people

### 5.3 Tree-aware search
- Once the Ancestry tree is imported, use it to drive smarter searches:
  - Identify people in the tree with **missing data** (no birth date, no death date, no parents) and auto-generate targeted searches for them
  - Prioritize "brick wall" ancestors (end-of-line with no parents) for research
  - Use known family context (siblings, spouses) to improve search accuracy
  - Cross-reference the tree against FamilySearch/FindAGrave to find records not yet attached

### 5.4 Ancestry Hints integration
- Generate URLs that link directly to Ancestry hint pages for specific people in the tree
- URL pattern: `https://www.ancestry.com/family-tree/person/tree/<TREE_ID>/person/<PERSON_ID>/hints`
- Help the user systematically work through unreviewed hints

---

## Phase 6: Fact Checker & Tree Quality Analyzer

### 6.1 Biological impossibility detection
- **Age at childbirth**: Flag if a mother is listed as <13 or >50, or a father is <13 or >75
- **Age at death**: Flag if lifespan exceeds 110 years or death is before birth
- **Age at marriage**: Flag if either spouse is <14 at marriage date
- **Birth after parent's death**: Flag if a child is born >9 months after father's death, or after mother's death
- **Duplicate people**: Detect likely duplicates (same name + similar dates) that should be merged

### 6.2 Chronological consistency checks
- **Event ordering**: Birth < Marriage < Death for each person
- **Date gaps**: Flag suspiciously large gaps (e.g., 20+ year gap between siblings suggesting a missing child)
- **Census consistency**: If a person appears in 1850 census age 10, they should appear in 1860 census age ~20 — flag mismatches
- **Location consistency**: Flag if a person is recorded in two distant places at implausible times (e.g., born in Ireland, married in Ohio 2 months later in 1830)

### 6.3 Source quality assessment
- Flag people/events with **no sources attached**
- Flag people whose only source is another user's tree (unreliable)
- Identify which facts are supported by primary sources (vital records, census) vs. secondary sources (compiled databases, other trees)
- Generate a **confidence score** per person: High (multiple primary sources), Medium (some sources), Low (no sources or tree-only)

### 6.4 Common genealogy mistakes detection
- **Wrong century**: Catch accidental 1900 vs 1800 typos (a parent born after their child)
- **Name spelling drift**: Flag when the same person has significantly different name spellings across records without explanation
- **Impossible locations**: Place names that didn't exist at the stated date (e.g., "West Virginia" before 1863)
- **Ethnicity/origin mismatches**: Flag when surname origin doesn't match stated birth country (could be legitimate but worth reviewing)
- **Too-perfect data**: Flag when every ancestor has exact birth/death dates going back to the 1600s (likely fabricated or unverified)

### 6.5 Tree completeness analysis
- Calculate **completeness percentage** per generation:
  - Generation 1 (parents): 2 people expected
  - Generation 2 (grandparents): 4 expected
  - Generation 3: 8 expected, etc.
- Identify which branches are well-researched vs. sparse
- Suggest which branch to focus research on next (the least complete one with the most potential records)

### 6.6 Fact check report
- Generate a structured report with issues categorized by severity:
  - **Errors** (red): Biological impossibilities, dates out of order
  - **Warnings** (yellow): Missing sources, suspicious gaps, low confidence data
  - **Suggestions** (blue): Missing data that could be found, unreviewed hints, merge candidates
- Output as JSON, HTML, or terminal-formatted text
- Include direct links to the relevant Ancestry tree pages for each flagged issue

---

## Phase 7: Multi-Person / Family Search

### 5.1 Batch search from CSV/JSON input
- Accept a CSV or JSON file with multiple people to search
- Run searches for each person across all providers
- Output combined results

### 5.2 Relative search
- Given a known person, auto-generate searches for likely relatives:
  - Parents: same last name, same place, birth_year - 25
  - Siblings: same last name, same place, birth_year ± 10
  - Spouse: same place, similar birth year, different last name (for female ancestors, search maiden name variations)
  - Children: same last name, same place, birth_year + 20-40

### 5.3 Census year targeting
- Auto-calculate which US/UK census years a person would appear in
- US Census: 1790, 1800, ..., 1950 (every 10 years)
- UK Census: 1841, 1851, ..., 1921 (every 10 years)
- Generate targeted census search URLs

---

## Phase 8: Web UI

### 6.1 Build the search form (`formTemplate.html`)
- Input fields: first name, last name, place (with autocomplete), year
- Radio buttons for record type: All, Birth, Marriage, Death, Census, Military
- Checkboxes for which sites to search
- "Estimate relatives" toggle

### 6.2 Results dashboard (`index.html`)
- Display generated search URLs as clickable links (grouped by site)
- Show genealogy estimates panel:
  - Estimated generational timeline
  - Suggested census years to search
  - Likely migration patterns
- Simple family tree visualization (expandable nodes)

### 6.3 Backend API
- Use Flask or FastAPI to serve the web UI
- Endpoints:
  - `POST /search` - run a search, return URLs and estimates
  - `POST /estimate` - return genealogy estimates for a person
  - `POST /tree` - add/get family tree data
  - `GET /tree/export` - export tree as GEDCOM

---

## Implementation Priority / Suggested Order

| Priority | Phase | Effort | Impact |
|----------|-------|--------|--------|
| 1        | Phase 1 (Modernize) | Low | High - fixes broken code |
| 2        | Phase 3 (Data model) | Medium | High - enables everything else |
| 3        | Phase 3.4 (GEDCOM import/export) | Medium | High - needed for Ancestry import |
| 4        | Phase 5.1 (Ancestry GEDCOM import) | Low | **Very High** - uses your existing tree |
| 5        | Phase 6.1-6.2 (Fact checker: impossibilities + chronology) | Medium | **Very High** - catches tree errors |
| 6        | Phase 6.3-6.5 (Source quality + completeness) | Medium | High - prioritizes research |
| 7        | Phase 2.1-2.2 (FamilySearch + FindAGrave) | Low | High - 2 major free sources |
| 8        | Phase 4.1-4.2 (Generation + Lifespan estimates) | Medium | High - core differentiator |
| 9        | Phase 5.3 (Tree-aware search) | Medium | **Very High** - auto-fills gaps |
| 10       | Phase 4.4 (Search year ranges) | Low | High - smart search automation |
| 11       | Phase 6.6 (Fact check report) | Low | High - actionable output |
| 12       | Phase 7.2 (Relative search) | Medium | High - automates discovery |
| 13       | Phase 2.3-2.4 (More providers) | Medium | Medium |
| 14       | Phase 4.3 (Migration patterns) | Medium | Medium |
| 15       | Phase 8 (Web UI) | High | Medium - nice to have |
| 16       | Phase 5.2 (Ancestry API/scraping) | High | Medium - complex, may break |
| 17       | Phase 7.1 (Batch search) | Low | Low |

---

## File Structure (Proposed)

```
genSearch/
├── gensearch/                  # Python package
│   ├── __init__.py
│   ├── cli.py                  # argparse-based CLI entry point
│   ├── models.py               # Person, Relationship, FamilyTree
│   ├── estimates.py            # Genealogy estimation engine
│   ├── search.py               # Search orchestrator
│   ├── providers/              # Search provider plugins
│   │   ├── __init__.py
│   │   ├── base.py             # SearchProvider base class
│   │   ├── ancestry.py
│   │   ├── familysearch.py
│   │   ├── findmypast.py
│   │   ├── findagrave.py
│   │   └── billiongraves.py
│   ├── tree_import/            # Tree import from external sources
│   │   ├── __init__.py
│   │   ├── gedcom_parser.py    # GEDCOM file import/export
│   │   └── ancestry_import.py  # Ancestry-specific import helpers
│   ├── fact_checker/           # Tree quality & fact checking
│   │   ├── __init__.py
│   │   ├── checks.py           # Individual check functions
│   │   ├── rules.py            # Configurable thresholds & rules
│   │   ├── report.py           # Report generation (JSON/HTML/text)
│   │   └── completeness.py     # Tree completeness analysis
│   └── utils.py                # URL encoding, date math
├── web/                        # Web UI
│   ├── app.py                  # Flask/FastAPI app
│   ├── templates/
│   │   ├── index.html
│   │   ├── form.html
│   │   └── report.html         # Fact check report view
│   └── static/
│       ├── style.css
│       └── app.js
├── tests/
│   ├── test_estimates.py
│   ├── test_providers.py
│   ├── test_models.py
│   ├── test_fact_checker.py
│   └── test_gedcom.py
├── sample_data/
│   └── sample.ged              # Sample GEDCOM for testing
├── requirements.txt
├── setup.py
└── README.md
```
