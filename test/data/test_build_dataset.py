import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch
import json

from src.data.build_dataset import (
    _parse_maturity,
    list_resources,
    _parse_sections,
    _parse_examples,
    _parse_documentation,
    load_processed_documents,
)


class TestParseMaturity:

    @pytest.mark.parametrize("value, expected", [
        ("3",  3),
        ("0",  0),
        ("N",  5),
        ("",   5),
        (None, 5),
        (2,    2),
    ])
    def test_known_inputs(self, value, expected):
        assert _parse_maturity(value) == expected


class TestGetTargetedResources:

    def _make_csv(self, tmp_path, rows: list[dict]) -> Path:
        path = tmp_path / "resources.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def test_filters_by_group(self, tmp_path):
        path = self._make_csv(tmp_path, [
            {"Resource": "Patient",   "GroupName": "Clinical",    "MaturityLevel": "3"},
            {"Resource": "Ignored",   "GroupName": "Informative", "MaturityLevel": "3"},
        ])
        assert list_resources(path) == ["patient"]

    def test_excludes_zero_maturity(self, tmp_path):
        path = self._make_csv(tmp_path, [
            {"Resource": "Patient", "GroupName": "Clinical", "MaturityLevel": "0"},
        ])
        assert list_resources(path) == []

    def test_unknown_maturity_treated_as_5(self, tmp_path):
        path = self._make_csv(tmp_path, [
            {"Resource": "Patient", "GroupName": "Clinical", "MaturityLevel": "N"},
        ])
        assert list_resources(path) == ["patient"]

    def test_deduplicates_and_sorts(self, tmp_path):
        path = self._make_csv(tmp_path, [
            {"Resource": "Patient",     "GroupName": "Clinical", "MaturityLevel": "3"},
            {"Resource": "patient",     "GroupName": "Base",     "MaturityLevel": "2"},
            {"Resource": "Observation", "GroupName": "Clinical", "MaturityLevel": "1"},
        ])
        assert list_resources(path) == ["observation", "patient"]

    def test_drops_na_resources(self, tmp_path):
        path = self._make_csv(tmp_path, [
            {"Resource": None,      "GroupName": "Clinical", "MaturityLevel": "3"},
            {"Resource": "Patient", "GroupName": "Clinical", "MaturityLevel": "3"},
        ])
        assert list_resources(path) == ["patient"]


class TestParseSections:

    def test_extracts_description_without_cutoff(self):
        sections = {"introduction": "Short intro. This resource is referenced elsewhere."}
        result = _parse_sections(sections)
        assert result["description"] == "Short intro."

    def test_empty_introduction(self):
        result = _parse_sections({})
        assert result["description"] == ""
        assert result["usage"] == ""
        assert result["extra"] == ""

    def test_extra_excludes_known_keys(self):
        sections = {
            "introduction": "intro",
            "Scope and Usage": "usage",
            "title": "Patient",
            "Boundaries": "some boundary text",
        }
        result = _parse_sections(sections)
        assert "some boundary text" in result["extra"]
        assert "intro" not in result["extra"]
        assert "usage" not in result["extra"]


class TestParseExamples:

    def test_formats_sentences(self):
        examples = [{"name": "General Patient"}, {"name": "Minimal Patient"}]
        result = _parse_examples(examples, "patient")
        assert result == [
            "General Patient is an example of patient",
            "Minimal Patient is an example of patient",
        ]

    def test_empty_examples(self):
        assert _parse_examples([], "patient") == []


class TestParseDocumentation:

    def test_formats_with_field_only(self):
        doc = {"Patient.id": "the logical id", "Patient.name": "a name"}
        result = _parse_documentation(doc)
        assert "id: the logical id" in result
        assert "name: a name" in result

    def test_top_level_key_kept_as_is(self):
        doc = {"Patient": "the root resource"}
        result = _parse_documentation(doc)
        assert "Patient: the root resource" in result

    def test_empty_documentation(self):
        assert _parse_documentation({}) == []


class TestLoadProcessedDocuments:

    def test_loads_and_serialises(self, tmp_path):
        res_dir = tmp_path / "patient"
        res_dir.mkdir()
        (res_dir / "patient.json").write_text(json.dumps({
            "resource": "patient",
            "examples": [{"name": "General Patient"}],
            "sections": {"introduction": "A patient.", "Scope and Usage": "Used for..."},
            "definitions": {"Patient.id": "logical id"},
        }), encoding="utf-8")

        result = load_processed_documents(tmp_path)
        assert len(result) == 1
        parsed = json.loads(result[0])
        assert parsed["resource"] == "patient"
        assert "description" in parsed
        assert "examples" in parsed

    def test_returns_empty_on_empty_dir(self, tmp_path):
        assert load_processed_documents(tmp_path) == []