"""FamilySearch.org search provider."""

from urllib.parse import quote_plus, quote
from .base import SearchProvider


class FamilySearchProvider(SearchProvider):

    @property
    def name(self) -> str:
        return "FamilySearch"

    @property
    def base_url(self) -> str:
        return "https://www.familysearch.org/search/record/results"

    def build_url(self, first: str, last: str, place: str = "", year: str = "") -> str:
        # FamilySearch uses a query parameter with a special syntax
        query_parts = [
            f"+givenname:{quote(first, safe='')}",
            f"+surname:{quote(last, safe='')}",
        ]
        if place:
            query_parts.append(f'+birth_place:"{quote(place, safe="")}"~')
        if year:
            query_parts.append(f"+birth_year:{year}-{year}~")

        query = " ".join(query_parts)
        return f"{self.base_url}?count=20&query={quote_plus(query)}"
