"""
Scraping utilities for the HL7 FHIR R4 documentation.
"""

from itertools import takewhile
import json
from pathlib import Path
import re

import requests
from bs4 import BeautifulSoup
from src.data.resources import load_resources

def _parse_example_links(soup: BeautifulSoup, base_url: str) -> list[dict]:
    table = soup.find("table", {"class": "list"})
    if not table:
        return []

    def extract_row(row):
        cells = row.find_all("td")
        if len(cells) < 4:
            return None
        name = cells[0].get_text(strip=True)
        link = cells[3].find("a", href=lambda h: h and h.endswith(".html"))
        if not name or not link:
            return None
        json_url = f"{base_url}/{link['href'].replace('.html', '')}"
        return {"name": name, "json_url": json_url}

    rows = table.find_all("tr")[1:]  # skip header
    return [r for r in map(extract_row, rows) if r is not None]


def _fetch_example(resource: str, example: dict) -> dict | None:
    try:
        r = requests.get(example["json_url"], timeout=10)
        r.raise_for_status()
        doc = r.json()
        return (
            {"name": example["name"], "document": doc}
            if doc.get("resourceType", "").lower() == resource
            else None
        )
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"[WARN] {example['json_url']} → {e}")
        return None


def fetch_examples(resource: str) -> list[dict]:
    """
    Fetch all available JSON examples for a given FHIR R4 resource.

    Retrieves the available examples for the specified resource, extracts all
    valid example links, and fetches each one as a JSON document. Only
    examples whose ``resourceType`` matches the requested resource are returned.

    Parameters
    ----------
    resource : str
        The FHIR R4 resource name in lowercase (e.g. ``"patient"``, ``"observation"``).

    Returns
    -------
    list[dict]
        A list of dicts, each with the following keys:

        - ``name`` (str): Human-readable example name as shown on the FHIR page.
        - ``document`` (dict): The full parsed JSON document of the example.

        Returns an empty list if the examples page has no valid table or
        no examples match the resource type.

    Raises
    ------
    requests.HTTPError
        If the examples page returns a non-2xx HTTP status code.

    Examples
    --------
    >>> examples = fetch_examples("patient")
    >>> examples[0]
    {
        "name": "General Person Example",
        "document": {"resourceType": "Patient", "id": "example", ...}
    }

    Notes
    -----
    - Individual example fetches that fail (network error, malformed JSON,
      wrong resource type) are silently skipped with a ``[WARN]`` log to stdout.
    - Delegates HTML parsing to :func:`_parse_example_links` and individual
      fetches to :func:`_fetch_example`.
    """
    base_url = "https://hl7.org/fhir/R4"
    soup = _get_soup(f"{base_url}/{resource}-examples.html")
    links = _parse_example_links(soup, base_url)

    return [
        result
        for result in (_fetch_example(resource, ex) for ex in links)
        if result is not None
    ]

def _get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def _siblings_until(tag, stop_tag: str, collect_tags: tuple[str]) -> list[str]:
    return [
        sib.get_text(" ", strip=True)
        for sib in takewhile(
            lambda s: s.name != stop_tag,
            tag.find_next_siblings()
        )
        if sib.name in collect_tags
    ]


def _parse_definitions_from_soup(soup: BeautifulSoup) -> dict[str, str]:

    def extract_pair(table) -> dict[str, str]:
        pairs = {}
        element_id = definition = None
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            key, value = cells[0].get_text(strip=True), cells[1].get_text(strip=True)
            element_id = value if key == "Element Id" else element_id
            definition = value.lower() if key == "Definition" else definition
            if element_id and definition:
                pairs[element_id] = definition
                element_id = definition = None
        return pairs

    return {
        k: v
        for table in soup.find_all("table")
        for k, v in extract_pair(table).items()
    }


def fetch_definitions(resource: str) -> dict[str, str]:
    """
    Fetch all element definitions for a given FHIR R4 resource.

    Retrieves the definitions page for the specified resource and extracts
    all element ID → definition pairs from its tables.

    Parameters
    ----------
    resource : str
        The FHIR R4 resource name in lowercase (e.g. ``"patient"``, ``"observation"``).

    Returns
    -------
    dict[str, str]
        A dict mapping each element ID to its definition, e.g.::

            {
                "Patient.id":        "the logical id of the resource...",
                "Patient.birthDate": "the date of birth for the individual...",
                ...
            }

        Returns an empty dict if no valid tables are found on the page.

    Raises
    ------
    requests.HTTPError
        If the definitions page returns a non-2xx HTTP status code.

    Examples
    --------
    >>> defs = fetch_definitions("patient")
    >>> defs["Patient.birthDate"]
    'the date of birth for the individual.'

    Notes
    -----
    - All definition values are lowercased at parse time.
    - Delegates HTML parsing to :func:`_parse_definitions_from_soup`.
    """
    soup = _get_soup(f"https://hl7.org/fhir/R4/{resource}-definitions.html")
    return _parse_definitions_from_soup(soup)


def fetch_description_section(resource: str) -> dict[str, str]:
    """
    Fetch the structured description page for a given FHIR R4 resource.

    Retrieves the main resource page and extracts the title, introduction,
    and all relevant content sections. Sections not useful for downstream
    processing (``"Resource Content"`` and ``"Search Parameters"``) are
    excluded automatically.

    Parameters
    ----------
    resource : str
        The FHIR R4 resource name in lowercase (e.g. ``"patient"``, ``"observation"``).

    Returns
    -------
    dict[str, str]
        A dict with the following guaranteed keys:

        - ``title`` (str | None): The text of the page ``<h1>`` tag,
          or ``None`` if not found.
        - ``introduction`` (str): First paragraph of the resource description.
          Empty string if no introductory paragraph is present.

        Plus one additional key per valid ``<h2>`` section found on the page,
        e.g.::

            {
                "title":         "Patient",
                "introduction":  "Demographics and other administrative information...",
                "Scope and Usage":   "...",
                "Boundaries and Relationships": "...",
            }

        Sections with no extractable content (no ``<p>``, ``<ul>`` or ``<ol>``
        siblings) are omitted entirely.

    Raises
    ------
    requests.HTTPError
        If the resource page returns a non-2xx HTTP status code.
    AttributeError
        If the page contains no ``<h1>`` tag and sibling traversal is attempted.

    Examples
    --------
    >>> sections = fetch_description_section("observation")
    >>> sections["title"]
    'Observation'
    >>> "Scope and Usage" in sections
    True

    Notes
    -----
    - Only the first introductory paragraph is captured for ``introduction``;
      subsequent pre-h2 paragraphs are ignored.
    - Section titles are stripped of all digits, dots, and colons via
      ``re.sub(r"[\\d.:]", "", ...)``, so numbering like ``"2.1"`` is removed.
    - Delegates page fetching to :func:`_get_soup` and sibling collection
      to :func:`_siblings_until`.
    """

    soup = _get_soup(f"https://hl7.org/fhir/R4/{resource}.html")

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else None
    introduction = "\n".join(_siblings_until(h1, stop_tag="h2", collect_tags=("p",))[:1])

    excluded_titles = {"Resource Content", "Search Parameters"}

    def is_valid_section(h2) -> bool:
        return not any(exc in re.sub(r"[\d.:]",
                                     "",
                                     h2.get_text(strip=True)) for exc in excluded_titles)

    def parse_section(h2) -> tuple[str, str] | None:
        section_title = re.sub(r"[\d.:]", "", h2.get_text(strip=True))
        content = _siblings_until(h2, stop_tag="h2", collect_tags=("p", "ul", "ol"))
        return (section_title, "\n".join(content)) if content else None

    sections = {
        title: content
        for h2 in filter(is_valid_section, soup.find_all("h2"))
        for title, content in [parsed for parsed in [parse_section(h2)] if parsed]
    }

    return {"title": title, "introduction": introduction, **sections}

def _scrape_resource(resource: str) -> dict:
    """Fetch all data for a single FHIR resource and return it as a dict."""
    return {
        "resource":      resource,
        "examples":      fetch_examples(resource),
        "sections":      fetch_description_section(resource),
        "definitions":   fetch_definitions(resource),
    }


def _save_resource(data: dict, docs_dir: Path) -> None:
    """Persist a resource dict to its own JSON file under docs_dir."""
    resource = data["resource"]
    out_dir  = docs_dir / resource
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{resource}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _is_already_scraped(resource: str, docs_dir: Path) -> bool:
    return (docs_dir / resource / f"{resource}.json").exists()


def scrape_all_resources(resources_path: Path, docs_dir: Path) -> None:
    """
    Scrape all targeted FHIR resources and save each as a JSON file.

    Skips resources that have already been scraped. Prints progress
    and warnings to stdout.

    Parameters
    ----------
    resources_path : Path
        Path to the CSV file listing FHIR resources to process.
    docs_dir : Path
        Root output directory; one sub-folder is created per resource.
    """
    docs_dir.mkdir(parents=True, exist_ok=True)
    resources = load_resources(resources_path)

    pending = [r for r in resources if not _is_already_scraped(r, docs_dir)]
    skipped = len(resources) - len(pending)

    print(f"{len(pending)} resources to scrape, {skipped} already present\n")

    for resource in pending:
        print(f"  processing {resource} ...")
        try:
            data = _scrape_resource(resource)
            _save_resource(data, docs_dir)
        except (requests.exceptions.RequestException, AttributeError) as e:
            print(f"  [WARN] {resource} failed: {e}")
