# from unittest.mock import MagicMock, patch, mock_open
# from bs4 import BeautifulSoup
# from pathlib import Path
# import json
# import pytest

# from src.data.scraper import (
#     _parse_example_links,
#     _fetch_example,
#     _parse_definitions_from_soup,
#     _siblings_until,
#     fetch_examples,
#     fetch_definitions,
#     fetch_description_section,
#     _scrape_resource,
#     _save_resource,
#     _is_already_scraped,
# )

# FIXTURES = Path(__file__).parent / "fixtures"

# def make_soup(html: str) -> BeautifulSoup:
#     return BeautifulSoup(html, "html.parser")


# class TestParseExampleLinks:

#     def test_returns_empty_when_no_table(self):
#         soup = make_soup("<html><body></body></html>")
#         assert _parse_example_links(soup, "https://hl7.org/fhir/R4") == []

#     def test_parses_valid_row(self):
#         html = """
#         <table class="list">
#           <tr><th>Name</th></tr>
#           <tr>
#             <td>General Patient</td>
#             <td></td><td></td>
#             <td><a href="patient-example.html">JSON</a></td>
#           </tr>
#         </table>
#         """
#         result = _parse_example_links(make_soup(html), "https://base")
#         assert len(result) == 1
#         assert result[0]["name"] == "General Patient"
#         assert result[0]["json_url"] == "https://base/patient-example"

#     def test_skips_row_with_missing_link(self):
#         html = """
#         <table class="list">
#           <tr><th>Name</th></tr>
#           <tr>
#             <td>No Link</td>
#             <td></td><td></td>
#             <td></td>
#           </tr>
#         </table>
#         """
#         result = _parse_example_links(make_soup(html), "https://base")
#         assert result == []

#     def test_skips_row_with_too_few_cells(self):
#         html = """
#         <table class="list">
#           <tr><td>Only one cell</td></tr>
#         </table>
#         """
#         assert _parse_example_links(make_soup(html), "https://base") == []

#     def test_real_html_fixture(self, examples_html):
#         """Smoke test: real FHIR page must return at least one example."""
#         soup = make_soup(examples_html)
#         result = _parse_example_links(soup, "https://hl7.org/fhir/R4")
#         assert len(result) > 0
#         assert all("name" in r and "json_url" in r for r in result)


# class TestFetchExample:

#     def test_returns_none_on_wrong_resource_type(self):
#         mock_response = MagicMock()
#         mock_response.json.return_value = {"resourceType": "Observation"}
#         mock_response.raise_for_status = MagicMock()

#         with patch("src.data.scraper.requests.get", return_value=mock_response):
#             result = _fetch_example("patient", {"name": "X", "json_url": "https://x"})

#         assert result is None

#     def test_returns_dict_on_matching_resource_type(self):
#         doc = {"resourceType": "Patient", "id": "example"}
#         mock_response = MagicMock()
#         mock_response.json.return_value = doc
#         mock_response.raise_for_status = MagicMock()

#         with patch("src.data.scraper.requests.get", return_value=mock_response):
#             result = _fetch_example("patient", {"name": "Test", "json_url": "https://x"})

#         assert result == {"name": "Test", "document": doc}

#     def test_returns_none_and_warns_on_exception(self, capsys):
#         with patch("src.data.scraper.requests.get", side_effect=ConnectionError("timeout")):
#             result = _fetch_example("patient", {"name": "X", "json_url": "https://x"})

#         assert result is None
#         assert "[WARN]" in capsys.readouterr().out


# class TestParseDefinitionsFromSoup:

#     def test_extracts_element_id_and_definition(self):
#         html = """
#         <table>
#           <tr><td>Element Id</td><td>Patient.id</td></tr>
#           <tr><td>Definition</td><td>The logical ID</td></tr>
#         </table>
#         """
#         result = _parse_definitions_from_soup(make_soup(html))
#         assert result == {"Patient.id": "the logical id"}

#     def test_returns_empty_on_no_tables(self):
#         assert _parse_definitions_from_soup(make_soup("<html></html>")) == {}

#     def test_ignores_incomplete_pairs(self):
#         html = """
#         <table>
#           <tr><td>Element Id</td><td>Patient.name</td></tr>
#         </table>
#         """
#         result = _parse_definitions_from_soup(make_soup(html))
#         assert result == {}

#     def test_lowercases_definition(self):
#         html = """
#         <table>
#           <tr><td>Element Id</td><td>Patient.status</td></tr>
#           <tr><td>Definition</td><td>ACTIVE OR INACTIVE</td></tr>
#         </table>
#         """
#         result = _parse_definitions_from_soup(make_soup(html))
#         assert result["Patient.status"] == "active or inactive"

#     def test_real_html_fixture(self, definitions_html):
#         soup = make_soup(definitions_html)
#         result = _parse_definitions_from_soup(soup)
#         assert len(result) > 0
#         assert all(isinstance(v, str) for v in result.values())


# class TestSiblingsUntil:

#     def test_collects_paragraphs_until_h2(self):
#         html = "<div><h1>Title</h1><p>First</p><p>Second</p><h2>Stop</h2><p>After</p></div>"
#         soup = make_soup(html)
#         result = _siblings_until(soup.find("h1"), stop_tag="h2", collect_tags=("p",))
#         assert result == ["First", "Second"]

#     def test_returns_empty_when_no_matching_tags(self):
#         html = "<div><h1>Title</h1><h2>Immediate stop</h2></div>"
#         soup = make_soup(html)
#         result = _siblings_until(soup.find("h1"), stop_tag="h2", collect_tags=("p",))
#         assert result == []

#     def test_collects_multiple_tag_types(self):
#         html = "<div><h2>Start</h2><p>Para</p><ul><li>item</li></ul><h2>End</h2></div>"
#         soup = make_soup(html)
#         result = _siblings_until(soup.find("h2"), stop_tag="h2", collect_tags=("p", "ul"))
#         assert len(result) == 2



# class TestFetchDescriptionSection:

#     def test_returns_title_and_introduction(self, description_html):
#         with patch("src.data.scraper._get_soup", return_value=make_soup(description_html)):
#             result = fetch_description_section("patient")
#         assert result["title"] is not None
#         assert "introduction" in result

#     def test_excludes_resource_content_and_search_parameters(self, description_html):
#         with patch("src.data.scraper._get_soup", return_value=make_soup(description_html)):
#             result = fetch_description_section("patient")
#         assert "Resource Content" not in result
#         assert "Search Parameters" not in result

#     def test_section_titles_stripped_of_numbering(self, description_html):
#         with patch("src.data.scraper._get_soup", return_value=make_soup(description_html)):
#             result = fetch_description_section("patient")
#         for key in result:
#             assert not any(c.isdigit() for c in key)


# class TestSaveAndCheck:

#     def test_save_creates_json_file(self, tmp_path):
#         data = {"resource": "patient", "examples": [], "sections": {}, "definitions": {}}
#         _save_resource(data, tmp_path)
#         out = tmp_path / "patient" / "patient.json"
#         assert out.exists()
#         assert json.loads(out.read_text())["resource"] == "patient"

#     def test_is_already_scraped_true(self, tmp_path):
#         (tmp_path / "patient").mkdir()
#         (tmp_path / "patient" / "patient.json").write_text("{}")
#         assert _is_already_scraped("patient", tmp_path) is True

#     def test_is_already_scraped_false(self, tmp_path):
#         assert _is_already_scraped("patient", tmp_path) is False