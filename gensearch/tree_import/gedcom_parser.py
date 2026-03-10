"""GEDCOM file parser and exporter.

Supports GEDCOM 5.5/5.5.1 — the standard genealogy interchange format.
Ancestry, FamilySearch, RootsMagic, and most tools export this format.
"""

import re
from typing import Optional, TextIO

from gensearch.models import (
    Person, Event, Source, Relationship, FamilyTree,
    Gender, RelationType, SourceType,
)


def _parse_year(date_str: str) -> Optional[int]:
    """Extract a year from a GEDCOM date string like 'ABT 1850' or '15 MAR 1892'."""
    match = re.search(r'\b(\d{4})\b', date_str)
    return int(match.group(1)) if match else None


def _parse_gender(value: str) -> Gender:
    value = value.strip().upper()
    if value == "M":
        return Gender.MALE
    elif value == "F":
        return Gender.FEMALE
    return Gender.UNKNOWN


class GedcomParser:
    """Parse a GEDCOM file into a FamilyTree."""

    def __init__(self):
        self._individuals = {}   # xref_id -> dict of parsed fields
        self._families = {}      # xref_id -> dict of parsed fields
        self._sources = {}       # xref_id -> Source

    def parse_file(self, filepath: str) -> FamilyTree:
        """Parse a GEDCOM file and return a FamilyTree."""
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return self.parse(f)

    def parse(self, stream: TextIO) -> FamilyTree:
        """Parse a GEDCOM stream and return a FamilyTree."""
        lines = stream.readlines()
        self._parse_records(lines)
        return self._build_tree()

    def _parse_records(self, lines):
        """First pass: group lines into individual/family/source records."""
        current_record = None
        current_xref = None
        current_tag = None
        sub_tag = None

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            parts = line.split(" ", 2)
            level = int(parts[0])

            if level == 0:
                # New top-level record
                if len(parts) >= 3 and parts[2] == "INDI":
                    current_xref = parts[1].strip("@")
                    current_record = "INDI"
                    self._individuals[current_xref] = {
                        "name": "", "given": "", "surname": "",
                        "gender": Gender.UNKNOWN,
                        "events": [], "sources": [],
                    }
                elif len(parts) >= 3 and parts[2] == "FAM":
                    current_xref = parts[1].strip("@")
                    current_record = "FAM"
                    self._families[current_xref] = {
                        "husb": None, "wife": None, "children": [],
                        "marriage_date": None, "marriage_place": None,
                    }
                elif len(parts) >= 3 and parts[2] == "SOUR":
                    current_xref = parts[1].strip("@")
                    current_record = "SOUR"
                    self._sources[current_xref] = {"title": ""}
                else:
                    current_record = None
                    current_xref = None
                current_tag = None
                sub_tag = None
                continue

            if current_record is None:
                continue

            tag = parts[1] if len(parts) >= 2 else ""
            value = parts[2] if len(parts) >= 3 else ""

            if current_record == "INDI":
                self._parse_indi_line(current_xref, level, tag, value)
            elif current_record == "FAM":
                self._parse_fam_line(current_xref, level, tag, value)
            elif current_record == "SOUR":
                self._parse_sour_line(current_xref, level, tag, value)

    def _parse_indi_line(self, xref, level, tag, value):
        indi = self._individuals[xref]

        if level == 1:
            indi["_current_tag"] = tag
            if tag == "NAME":
                indi["name"] = value.strip("/")
            elif tag == "SEX":
                indi["gender"] = _parse_gender(value)
            elif tag in ("BIRT", "DEAT", "BURI", "CHR", "RESI"):
                event_type_map = {
                    "BIRT": "birth", "DEAT": "death", "BURI": "burial",
                    "CHR": "christening", "RESI": "residence",
                }
                indi["_current_event"] = {
                    "type": event_type_map.get(tag, tag.lower()),
                    "date": None, "place": None, "year": None,
                }
                indi["events"].append(indi["_current_event"])
            elif tag == "SOUR":
                source_xref = value.strip("@")
                indi["sources"].append(source_xref)
        elif level == 2:
            current = indi.get("_current_tag", "")
            if tag == "GIVN":
                indi["given"] = value
            elif tag == "SURN":
                indi["surname"] = value
            elif tag == "DATE" and "_current_event" in indi:
                indi["_current_event"]["date"] = value
                indi["_current_event"]["year"] = _parse_year(value)
            elif tag == "PLAC" and "_current_event" in indi:
                indi["_current_event"]["place"] = value

    def _parse_fam_line(self, xref, level, tag, value):
        fam = self._families[xref]
        if level == 1:
            fam["_current_tag"] = tag
            if tag == "HUSB":
                fam["husb"] = value.strip("@")
            elif tag == "WIFE":
                fam["wife"] = value.strip("@")
            elif tag == "CHIL":
                fam["children"].append(value.strip("@"))
            elif tag == "MARR":
                pass  # marriage event — date/place on level 2
        elif level == 2:
            if fam.get("_current_tag") == "MARR":
                if tag == "DATE":
                    fam["marriage_date"] = value
                elif tag == "PLAC":
                    fam["marriage_place"] = value

    def _parse_sour_line(self, xref, level, tag, value):
        if level == 1 and tag == "TITL":
            self._sources[xref]["title"] = value

    def _build_tree(self) -> FamilyTree:
        """Convert parsed records into a FamilyTree."""
        tree = FamilyTree(name="Imported GEDCOM")

        # Build Person objects
        for xref, indi in self._individuals.items():
            given = indi.get("given") or ""
            surname = indi.get("surname") or ""

            # Fallback: parse from NAME field "First /Last/"
            if not given and not surname and indi.get("name"):
                name_parts = indi["name"].replace("/", "").split()
                if name_parts:
                    given = name_parts[0]
                    surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            person = Person(
                id=xref,
                first_name=given,
                last_name=surname,
                gender=indi.get("gender", Gender.UNKNOWN),
            )

            # Attach events
            for evt in indi.get("events", []):
                event = Event(
                    event_type=evt["type"],
                    year=evt.get("year"),
                    date=evt.get("date"),
                    place=evt.get("place"),
                )
                person.events.append(event)

                # Set convenience fields
                if evt["type"] == "birth":
                    person.birth_year = evt.get("year")
                    person.birth_place = evt.get("place")
                elif evt["type"] == "death":
                    person.death_year = evt.get("year")
                    person.death_place = evt.get("place")

            # Attach sources
            for source_xref in indi.get("sources", []):
                if source_xref in self._sources:
                    src_data = self._sources[source_xref]
                    title = src_data.get("title", "Unknown source")
                    # Heuristic: if title contains "tree" it's a user tree source
                    source_type = SourceType.USER_TREE if "tree" in title.lower() else SourceType.UNKNOWN
                    person.sources.append(Source(title=title, source_type=source_type))

            tree.add_person(person)

        # Build relationships from FAM records
        for xref, fam in self._families.items():
            husb = fam.get("husb")
            wife = fam.get("wife")
            children = fam.get("children", [])

            # Spouse relationship
            if husb and wife:
                tree.add_relationship(Relationship(husb, wife, RelationType.SPOUSE))

            # Parent-child relationships
            for child_id in children:
                if husb:
                    tree.add_relationship(Relationship(child_id, husb, RelationType.PARENT))
                if wife:
                    tree.add_relationship(Relationship(child_id, wife, RelationType.PARENT))

        return tree


def export_gedcom(tree: FamilyTree, filepath: str) -> None:
    """Export a FamilyTree to a GEDCOM file."""
    with open(filepath, "w", encoding="utf-8") as f:
        # Header
        f.write("0 HEAD\n")
        f.write("1 SOUR genSearch\n")
        f.write("2 VERS 0.1.0\n")
        f.write("1 GEDC\n")
        f.write("2 VERS 5.5.1\n")
        f.write("2 FORM LINEAGE-LINKED\n")
        f.write("1 CHAR UTF-8\n")

        # Individuals
        for person in tree.members.values():
            f.write(f"0 @{person.id}@ INDI\n")
            f.write(f"1 NAME {person.first_name} /{person.last_name}/\n")
            f.write(f"2 GIVN {person.first_name}\n")
            f.write(f"2 SURN {person.last_name}\n")

            gender_char = {"male": "M", "female": "F"}.get(person.gender.value, "U")
            f.write(f"1 SEX {gender_char}\n")

            for event in person.events:
                tag_map = {
                    "birth": "BIRT", "death": "DEAT", "burial": "BURI",
                    "christening": "CHR", "residence": "RESI",
                }
                tag = tag_map.get(event.event_type, event.event_type.upper()[:4])
                f.write(f"1 {tag}\n")
                if event.date:
                    f.write(f"2 DATE {event.date}\n")
                elif event.year:
                    f.write(f"2 DATE {event.year}\n")
                if event.place:
                    f.write(f"2 PLAC {event.place}\n")

        # Families — reconstruct from relationships
        fam_id = 0
        processed_spouses = set()
        for rel in tree.relationships:
            if rel.relation_type == RelationType.SPOUSE:
                pair = tuple(sorted([rel.person_id, rel.related_to_id]))
                if pair in processed_spouses:
                    continue
                processed_spouses.add(pair)
                fam_id += 1
                fam_xref = f"F{fam_id}"
                f.write(f"0 @{fam_xref}@ FAM\n")

                p1 = tree.get_person(pair[0])
                p2 = tree.get_person(pair[1])
                if p1 and p2:
                    if p1.gender == Gender.MALE:
                        f.write(f"1 HUSB @{p1.id}@\n")
                        f.write(f"1 WIFE @{p2.id}@\n")
                    else:
                        f.write(f"1 HUSB @{p2.id}@\n")
                        f.write(f"1 WIFE @{p1.id}@\n")

                # Find children of this couple
                for member in tree.members.values():
                    parents = tree.get_parents(member.id)
                    parent_ids = {p.id for p in parents}
                    if pair[0] in parent_ids and pair[1] in parent_ids:
                        f.write(f"1 CHIL @{member.id}@\n")

        # Trailer
        f.write("0 TRLR\n")
