"""FindAGrave.com search provider."""

from urllib.parse import quote_plus
from .base import SearchProvider


class FindAGraveProvider(SearchProvider):

    @property
    def name(self) -> str:
        return "FindAGrave"

    @property
    def base_url(self) -> str:
        return "https://www.findagrave.com/memorial/search"

    def build_url(self, first: str, last: str, place: str = "", year: str = "") -> str:
        params = [
            f"firstname={quote_plus(first)}",
            f"lastname={quote_plus(last)}",
        ]
        if place:
            params.append(f"location={quote_plus(place)}")
        if year:
            params.append(f"birthyear={quote_plus(year)}")
            params.append("birthyearfilter=2")  # ± 2 years
        return f"{self.base_url}?{'&'.join(params)}"
