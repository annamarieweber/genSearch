"""FindMyPast.com search provider."""

from urllib.parse import quote_plus
from .base import SearchProvider


class FindMyPastProvider(SearchProvider):

    @property
    def name(self) -> str:
        return "FindMyPast"

    @property
    def base_url(self) -> str:
        return "https://search.findmypast.com/results/world-records"

    def build_url(self, first: str, last: str, place: str = "", year: str = "") -> str:
        params = [
            f"firstname={quote_plus(first)}",
            f"firstname_variants=true",
            f"lastname={quote_plus(last)}",
            f"lastname_variants=true",
        ]
        if place:
            params.append(f"keywordsplace={quote_plus(place)}")
        if year:
            params.append(f"eventyear={quote_plus(year)}")
            params.append("eventyear_offset=2")
        return f"{self.base_url}?{'&'.join(params)}"
