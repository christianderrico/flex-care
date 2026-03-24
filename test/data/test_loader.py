"""
Unit tests for the Loader class.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.data.loader import Loader

def _make_resource_json(tmp_path: Path, resource: str, payload: dict) -> Path:
    """Write a scraped resource JSON file in the expected directory layout."""
    resource_dir = tmp_path / resource
    resource_dir.mkdir(parents=True, exist_ok=True)
    fp = resource_dir / f"{resource}.json"
    fp.write_text(json.dumps(payload), encoding="utf-8")
    return fp


def _make_resources_csv(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "FHIR_resources.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _make_dataset_csv(tmp_path: Path, name: str, rows: list[dict]) -> Path:
    path = tmp_path / name
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _make_loader(tmp_path, resource_rows, doc_payloads: dict):
    """
    Instantiate a Loader with paths redirected to tmp_path.

    Parameters
    ----------
    resource_rows : list[dict]
        Rows for FHIR_resources.csv
    doc_payloads : dict
        Mapping resource_name -> JSON payload dict for the scraped docs.
    """

    docs_path = tmp_path / "Docs"
    dataset_dir = tmp_path
    resources_csv = _make_resources_csv(tmp_path, resource_rows)

    for resource, payload in doc_payloads.items():
        _make_resource_json(docs_path, resource, payload)

    loader = Loader(
        docs_path=docs_path,
        dataset_path=dataset_dir,
        resources_path=resources_csv
    )

    return loader

MINIMAL_PATIENT_PAYLOAD = {
    "resource": "patient",
    "sections": {
        "introduction": "A patient resource. This resource is referenced elsewhere.",
        "Scope and Usage": "Used for demographic info.",
        "Boundaries": "Does not cover practitioners.",
    },
    "examples": [{"name": "General Patient"}, {"name": "Minimal Patient"}],
    "documentation": {
        "Patient.id":         "the logical id",
        "Patient.name":       "a human name",
        "Patient":            "the root resource",
    },
}

BASE_RESOURCE_ROWS = [
    {"Resource": "Patient", "GroupName": "Clinical", "MaturityLevel": "3"},
]

class TestLoaderDocs:
    """Tests for Loader document generation."""

    def test_returns_one_document_per_resource(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        assert len(loader.docs) == 1

    def test_document_is_valid_json(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        parsed = json.loads(loader.docs[0])
        assert isinstance(parsed, dict)

    def test_document_contains_required_keys(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        parsed = json.loads(loader.docs[0])
        for key in ("resource", "description", "usage", "extra", "examples", "documentation"):
            assert key in parsed, f"Missing key: {key}"

    def test_description_is_truncated_at_cutoff(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        parsed = json.loads(loader.docs[0])
        assert "This resource is referenced" not in parsed["description"]
        assert parsed["description"] == "A patient resource."

    def test_usage_is_preserved(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        parsed = json.loads(loader.docs[0])
        assert parsed["usage"] == "Used for demographic info."

    def test_extra_excludes_intro_and_usage(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        parsed = json.loads(loader.docs[0])
        assert "A patient resource" not in parsed["extra"]
        assert "Used for demographic info" not in parsed["extra"]
        assert "Does not cover practitioners" in parsed["extra"]

    def test_examples_are_formatted_correctly(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        parsed = json.loads(loader.docs[0])
        assert "General Patient is an example of patient" in parsed["examples"]
        assert "Minimal Patient is an example of patient" in parsed["examples"]

    def test_documentation_strips_resource_prefix(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        parsed = json.loads(loader.docs[0])
        assert "id: the logical id" in parsed["documentation"]
        assert "name: a human name" in parsed["documentation"]

    def test_documentation_keeps_top_level_key(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        parsed = json.loads(loader.docs[0])
        assert "Patient: the root resource" in parsed["documentation"]

    def test_empty_docs_dir_raises_runtime_error(self, tmp_path):
        empty_docs = tmp_path / "Docs"
        empty_docs.mkdir()

        with pytest.raises(RuntimeError, match="No documents found"):
            Loader(docs_path=empty_docs)

    def test_docs_returns_a_copy(self, tmp_path):
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        assert loader.docs is not loader.docs

class TestLoaderLoadDataset:
    """Tests for Loader.load_dataset."""

    def test_returns_list_of_dicts(self, tmp_path):
        """Loader.docs should return one document per resource."""
        _make_dataset_csv(tmp_path, "eval.csv", [
            {"Field_description": "Patient age", "Mapping": "patient"},
        ])
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        result = loader.load_dataset("eval.csv")
        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)

    def test_record_has_text_and_ground_truth(self, tmp_path):
        """Docs record should have text and FHIR resource"""
        _make_dataset_csv(tmp_path, "eval.csv", [
            {"Field_description": "Patient age", "Mapping": "patient"},
        ])
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        record = loader.load_dataset("eval.csv")[0]
        assert "text" in record
        assert "ground_truth" in record

    def test_text_matches_field_description(self, tmp_path):
        """Test that the 'text' field matches the Field_description column."""
        _make_dataset_csv(tmp_path, "eval.csv", [
            {"Field_description": "Patient age", "Mapping": "patient"},
        ])
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        assert loader.load_dataset("eval.csv")[0]["text"] == "Patient age"

    def test_ground_truth_is_lowercase(self, tmp_path):
        """FHIR resource should be in lowercase"""
        _make_dataset_csv(tmp_path, "eval.csv", [
            {"Field_description": "Patient age", "Mapping": "Patient"},
        ])
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        assert loader.load_dataset("eval.csv")[0]["ground_truth"] == ["patient"]

    def test_ground_truth_strips_subpath(self, tmp_path):
        """Test that subpaths in the Mapping field are stripped to the base resource."""
        _make_dataset_csv(tmp_path, "eval.csv", [
            {"Field_description": "Patient name", "Mapping": "Patient.name"},
        ])
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        assert loader.load_dataset("eval.csv")[0]["ground_truth"] == ["patient"]

    def test_ground_truth_deduplicates_list_mapping(self, tmp_path):
        """Test that multiple mappings to the same resource are deduplicated."""
        _make_dataset_csv(tmp_path, "eval.csv", [
            {"Field_description": "Patient name", "Mapping": "['Patient.name', 'Patient.id']"},
        ])
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        result = loader.load_dataset("eval.csv")[0]["ground_truth"]
        assert result == ["patient"]

    def test_filters_out_unknown_resources(self, tmp_path):
        """Test filters out unknown resources"""
        _make_dataset_csv(tmp_path, "eval.csv", [
            {"Field_description": "Unknown field", "Mapping": "unknownresource"},
            {"Field_description": "Patient age",   "Mapping": "patient"},
        ])
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        result = loader.load_dataset("eval.csv")
        assert len(result) == 1
        assert result[0]["text"] == "Patient age"

    def test_raises_on_missing_file(self, tmp_path):
        """Test that loading a non-existent dataset file raises FileNotFoundError."""
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        with pytest.raises(FileNotFoundError):
            loader.load_dataset("nonexistent.csv")

    def test_empty_dataset_after_filtering(self, tmp_path):
        """Test that an empty list is returned if all records are filtered out."""
        _make_dataset_csv(tmp_path, "eval.csv", [
            {"Field_description": "Unknown field", "Mapping": "unknownresource"},
        ])
        loader = _make_loader(tmp_path, BASE_RESOURCE_ROWS, {"patient": MINIMAL_PATIENT_PAYLOAD})
        assert loader.load_dataset("eval.csv") == []
