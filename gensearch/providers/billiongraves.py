"""BillionGraves.com search provider."""

from urllib.parse import quote_plus
from .base import SearchProvider


class BillionGravesProvider(SearchProvider):

    @property
    def name(self) -> str:
        return "BillionGraves"

    @property
    def base_url(self) -> str:
        return "https://billiongraves.com/search"

    def build_url(self, first: str, last: str, place: str = "", year: str = "") -> str:
        params = [
            f"given_names={quote_plus(first)}",
            f"family_names={quote_plus(last)}",
        ]
        if year:
            params.append(f"birth_year={quote_plus(year)}")
            params.append("year_range=2")
        return f"{self.base_url}#{'&'.join(params)}"
