"""Data models for people, relationships, and family trees."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class RelationType(Enum):
    PARENT = "parent"
    CHILD = "child"
    SPOUSE = "spouse"
    SIBLING = "sibling"


class SourceType(Enum):
    PRIMARY = "primary"          # vital records, census, military
    SECONDARY = "secondary"      # compiled databases, books
    USER_TREE = "user_tree"      # another user's tree (least reliable)
    UNKNOWN = "unknown"


@dataclass
class Source:
    """A source backing a genealogical fact."""
    title: str
    source_type: SourceType = SourceType.UNKNOWN
    url: Optional[str] = None
    citation: Optional[str] = None


@dataclass
class Event:
    """A life event (birth, death, marriage, census, etc.)."""
    event_type: str                        # "birth", "death", "marriage", "census", etc.
    year: Optional[int] = None
    date: Optional[str] = None             # full date string if available
    place: Optional[str] = None
    sources: List[Source] = field(default_factory=list)


@dataclass
class Person:
    """Represents an individual in a family tree."""
    id: str
    first_name: str
    last_name: str
    gender: Gender = Gender.UNKNOWN

    # Core dates
    birth_year: Optional[int] = None
    birth_year_range: Optional[Tuple[int, int]] = None
    death_year: Optional[int] = None
    death_year_range: Optional[Tuple[int, int]] = None

    # Places
    birth_place: Optional[str] = None
    death_place: Optional[str] = None

    # All life events
    events: List[Event] = field(default_factory=list)

    # Sources attached to this person overall
    sources: List[Source] = field(default_factory=list)

    # Ancestry-specific IDs for linking back
    ancestry_tree_id: Optional[str] = None
    ancestry_person_id: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def birth_event(self) -> Optional[Event]:
        return next((e for e in self.events if e.event_type == "birth"), None)

    @property
    def death_event(self) -> Optional[Event]:
        return next((e for e in self.events if e.event_type == "death"), None)

    @property
    def estimated_birth_year(self) -> Optional[int]:
        """Best guess at birth year from exact or range."""
        if self.birth_year:
            return self.birth_year
        if self.birth_year_range:
            return (self.birth_year_range[0] + self.birth_year_range[1]) // 2
        return None

    @property
    def estimated_death_year(self) -> Optional[int]:
        if self.death_year:
            return self.death_year
        if self.death_year_range:
            return (self.death_year_range[0] + self.death_year_range[1]) // 2
        return None


@dataclass
class Relationship:
    """A directed relationship between two people."""
    person_id: str
    related_to_id: str
    relation_type: RelationType


class FamilyTree:
    """A collection of people and their relationships."""

    def __init__(self, name: str = "Untitled Tree"):
        self.name = name
        self.members: Dict[str, Person] = {}
        self.relationships: List[Relationship] = []

    def add_person(self, person: Person) -> None:
        self.members[person.id] = person

    def get_person(self, person_id: str) -> Optional[Person]:
        return self.members.get(person_id)

    def add_relationship(self, rel: Relationship) -> None:
        self.relationships.append(rel)

    def get_parents(self, person_id: str) -> List[Person]:
        """Get parents of a person."""
        parent_ids = [
            r.related_to_id for r in self.relationships
            if r.person_id == person_id and r.relation_type == RelationType.PARENT
        ]
        return [self.members[pid] for pid in parent_ids if pid in self.members]

    def get_children(self, person_id: str) -> List[Person]:
        """Get children of a person."""
        child_ids = [
            r.person_id for r in self.relationships
            if r.related_to_id == person_id and r.relation_type == RelationType.PARENT
        ]
        return [self.members[cid] for cid in child_ids if cid in self.members]

    def get_spouses(self, person_id: str) -> List[Person]:
        spouse_ids = [
            r.related_to_id for r in self.relationships
            if r.person_id == person_id and r.relation_type == RelationType.SPOUSE
        ]
        # Also check reverse direction
        spouse_ids += [
            r.person_id for r in self.relationships
            if r.related_to_id == person_id and r.relation_type == RelationType.SPOUSE
        ]
        return [self.members[sid] for sid in set(spouse_ids) if sid in self.members]

    def get_siblings(self, person_id: str) -> List[Person]:
        """Get siblings (people sharing at least one parent)."""
        parents = self.get_parents(person_id)
        siblings = set()
        for parent in parents:
            for child in self.get_children(parent.id):
                if child.id != person_id:
                    siblings.add(child.id)
        return [self.members[sid] for sid in siblings if sid in self.members]

    def get_ancestors(self, person_id: str, generations: int = 4) -> List[Person]:
        """Get ancestors up to N generations back."""
        if generations <= 0:
            return []
        parents = self.get_parents(person_id)
        ancestors = list(parents)
        for parent in parents:
            ancestors.extend(self.get_ancestors(parent.id, generations - 1))
        return ancestors

    def get_descendants(self, person_id: str, generations: int = 4) -> List[Person]:
        """Get descendants up to N generations forward."""
        if generations <= 0:
            return []
        children = self.get_children(person_id)
        descendants = list(children)
        for child in children:
            descendants.extend(self.get_descendants(child.id, generations - 1))
        return descendants

    def get_people_missing_data(self) -> Dict[str, List[Person]]:
        """Find people with incomplete data for targeted research."""
        missing = {
            "no_birth_year": [],
            "no_death_year": [],
            "no_birth_place": [],
            "no_parents": [],
            "no_sources": [],
        }
        for person in self.members.values():
            if not person.birth_year and not person.birth_year_range:
                missing["no_birth_year"].append(person)
            if not person.death_year and not person.death_year_range:
                missing["no_death_year"].append(person)
            if not person.birth_place:
                missing["no_birth_place"].append(person)
            if not self.get_parents(person.id):
                missing["no_parents"].append(person)
            if not person.sources:
                missing["no_sources"].append(person)
        return missing

    def get_brick_walls(self) -> List[Person]:
        """Find end-of-line ancestors with no parents — prime research targets."""
        walls = []
        for person in self.members.values():
            parents = self.get_parents(person.id)
            children = self.get_children(person.id)
            # Has children (not a leaf) but no parents (end of line)
            if not parents and (children or self.get_spouses(person.id)):
                walls.append(person)
        return walls

    def stats(self) -> Dict:
        """Return tree statistics."""
        return {
            "total_people": len(self.members),
            "total_relationships": len(self.relationships),
            "brick_walls": len(self.get_brick_walls()),
            "missing_birth_year": len([
                p for p in self.members.values()
                if not p.birth_year and not p.birth_year_range
            ]),
        }
