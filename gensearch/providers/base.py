"""Base class for genealogy search providers."""

from abc import ABC, abstractmethod


class SearchProvider(ABC):
    """Base class for all genealogy site search providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the provider."""

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base search URL for this provider."""

    @abstractmethod
    def build_url(self, first: str, last: str, place: str = "", year: str = "") -> str:
        """Build a search URL for the given person parameters.

        Args:
            first: First name
            last: Last name
            place: Location (city, state, country)
            year: Birth or approximate year

        Returns:
            Full search URL string
        """

    def build_ancestry_link(self, tree_id: str, person_id: str) -> str:
        """Build a direct link to a person in an Ancestry tree (only for Ancestry)."""
        return ""
