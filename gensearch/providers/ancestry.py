"""Ancestry.com search provider."""

from urllib.parse import quote_plus
from .base import SearchProvider


class AncestryProvider(SearchProvider):

    @property
    def name(self) -> str:
        return "Ancestry"

    @property
    def base_url(self) -> str:
        return "https://search.ancestry.com/cgi-bin/sse.dll"

    def build_url(self, first: str, last: str, place: str = "", year: str = "") -> str:
        params = [
            "gl=allgs",
            "gss=sfs28_ms_f-2_s",
            "new=1",
            "rank=1",
            "msT=1",
            f"gsfn={quote_plus(first)}",
            f"gsfn_x=0",
            f"gsln={quote_plus(last)}",
            f"gsln_x=0",
        ]
        if place:
            params.append(f"mswpn__ftp={quote_plus(place)}")
        if year:
            params.append(f"msbdy={quote_plus(year)}")
        params.append("MSAV=1")
        params.append("cp=0")
        params.append("catbucket=rstp")
        return f"{self.base_url}?{'&'.join(params)}"

    def build_tree_url(self, tree_id: str, person_id: str) -> str:
        """Direct link to a person in an Ancestry tree."""
        return f"https://www.ancestry.com/family-tree/person/tree/{tree_id}/person/{person_id}/facts"

    def build_hints_url(self, tree_id: str, person_id: str) -> str:
        """Direct link to hints for a person in an Ancestry tree."""
        return f"https://www.ancestry.com/family-tree/person/tree/{tree_id}/person/{person_id}/hints"
