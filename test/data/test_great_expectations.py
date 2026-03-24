"""
Data quality validation for the FHIR RAG mapping pipeline.
"""

import ast
import json
from pathlib import Path

import great_expectations as gx
import pandas as pd
import pytest

from src.data.resources import load_resources

DATASETS = {
    "MOTU":     Path("data/motu.csv"),
    "MIMIC-IV": Path("data/mimic.csv"),
    "SPHN":     Path("data/sphn.csv"),
}

FHIR_KB_DIR = Path("data/Docs")

ALL_FHIR_RESOURCES = set(
    pd.read_csv(Path("data/FHIR_resources.csv"))["Resource"]
    .dropna()
    .str.lower()
    .unique()
)

MIN_DESCRIPTION_LENGTH = 1
MIN_CHUNK_LENGTH = 20

def _make_batch(df: pd.DataFrame, source_name: str):
    """Registers a DataFrame as a GX ephemeral data source and returns (batch, context)."""
    context = gx.get_context()
    data_source = context.data_sources.add_pandas(name=source_name)
    data_asset = data_source.add_dataframe_asset(name=f"{source_name}_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe(
        f"{source_name}_batch"
    )
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
    return batch, context


def _run_suite(df: pd.DataFrame, source_name: str, suite_name: str, expectations: list) -> dict[str, bool]:
    """
    Adds expectations to a suite, validates the batch, and returns
    a dict mapping expectation type -> success.
    """
    batch, context = _make_batch(df, source_name)
    suite = gx.ExpectationSuite(name=suite_name)
    for expectation in expectations:
        suite.add_expectation(expectation)
    context.suites.add(suite)
    validation = batch.validate(suite)
    return {
        result["expectation_config"]["type"]: result["success"]
        for result in validation["results"]
    }


def _mapping_is_valid(value: str) -> bool:
    try:
        raw = ast.literal_eval(value) if str(value).strip().startswith("[") else [value]
        roots = {m.split(".")[0].lower() for m in raw}
        return bool(roots & ALL_FHIR_RESOURCES)
    except Exception:
        return False

def _load_eval_batch(path: Path, name: str):
    df = pd.read_csv(path)
    return df, name


@pytest.fixture
def motu():
    return _load_eval_batch(DATASETS["MOTU"], "motu")

@pytest.fixture
def mimic():
    return _load_eval_batch(DATASETS["MIMIC-IV"], "mimic")

@pytest.fixture
def sphn():
    return _load_eval_batch(DATASETS["SPHN"], "sphn")

@pytest.fixture
def fhir_kb():
    """
    Loads all scraped JSON resource files and returns
    (records_df, loaded_resources, source_name).
    """
    records = []
    loaded_resources = set()

    for resource_dir in FHIR_KB_DIR.iterdir():
        if not resource_dir.is_dir():
            continue
        for fp in resource_dir.glob("*.json"):
            resource_name = fp.stem.lower()
            loaded_resources.add(resource_name)
            raw = json.loads(fp.read_text(encoding="utf-8"))
            for key, value in raw.items():
                if key == "resource":
                    continue
                if isinstance(value, str) and value.strip():
                    records.append({"resource": resource_name, "content": value})
                elif isinstance(value, list):
                    for item in value:
                        content = item if isinstance(item, str) else json.dumps(item)
                        if content.strip():
                            records.append({"resource": resource_name, "content": content})

    df = pd.DataFrame(records)
    return df, loaded_resources, "fhir_kb"

@pytest.fixture(params=["motu", "mimic", "sphn"])
def eval_fixture(request, motu, mimic, sphn):
    return {"motu": motu, "mimic": mimic, "sphn": sphn}[request.param]

class TestEvalDatasetQuality:

    def test_field_description_column_exists(self, eval_fixture):
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_col_exists",
            [gx.expectations.ExpectColumnToExist(column="Field_description")])
        assert results["expect_column_to_exist"]

    def test_mapping_column_exists(self, eval_fixture):
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_mapping_exists",
            [gx.expectations.ExpectColumnToExist(column="Mapping")])
        assert results["expect_column_to_exist"]

    def test_no_null_field_descriptions(self, eval_fixture):
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_no_null_desc",
            [gx.expectations.ExpectColumnValuesToNotBeNull(column="Field_description")])
        assert results["expect_column_values_to_not_be_null"]

    def test_no_null_mappings(self, eval_fixture):
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_no_null_map",
            [gx.expectations.ExpectColumnValuesToNotBeNull(column="Mapping")])
        assert results["expect_column_values_to_not_be_null"]

    def test_description_min_length(self, eval_fixture):
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_desc_length",
            [gx.expectations.ExpectColumnValueLengthsToBeBetween(
                column="Field_description", min_value=MIN_DESCRIPTION_LENGTH
            )])
        assert results["expect_column_value_lengths_to_be_between"]

    def test_no_duplicate_rows(self, eval_fixture):
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_no_dupes",
            [gx.expectations.ExpectCompoundColumnsToBeUnique(
                column_list=list(df.columns)
            )])
        assert results["expect_compound_columns_to_be_unique"]

    def test_dataset_is_not_empty(self, eval_fixture):
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_not_empty",
            [gx.expectations.ExpectTableRowCountToBeBetween(min_value=1)])
        assert results["expect_table_row_count_to_be_between"]

    def test_all_mappings_are_valid_fhir_resources(self, eval_fixture):
        df, _ = eval_fixture
        invalid = df["Mapping"].apply(lambda v: not _mapping_is_valid(str(v))).sum()
        assert invalid == 0, f"{invalid} rows have mappings outside the valid FHIR resource set"


class TestFHIRKnowledgeBaseQuality:

    def test_kb_is_not_empty(self, fhir_kb):
        df, _, _ = fhir_kb
        assert len(df) > 0, "No chunks found in the FHIR knowledge base directory"

    def test_no_null_resource_identifiers(self, fhir_kb):
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_no_null_resource",
            [gx.expectations.ExpectColumnValuesToNotBeNull(column="resource")])
        assert results["expect_column_values_to_not_be_null"]

    def test_no_null_content(self, fhir_kb):
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_no_null_content",
            [gx.expectations.ExpectColumnValuesToNotBeNull(column="content")])
        assert results["expect_column_values_to_not_be_null"]

    def test_chunk_min_length(self, fhir_kb):
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_chunk_length",
            [gx.expectations.ExpectColumnValueLengthsToBeBetween(
                column="content", min_value=MIN_CHUNK_LENGTH
            )])
        assert results["expect_column_value_lengths_to_be_between"]

    def test_all_resource_names_are_valid(self, fhir_kb):
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_valid_resources",
            [gx.expectations.ExpectColumnValuesToBeInSet(
                column="resource", value_set=ALL_FHIR_RESOURCES
            )])
        assert results["expect_column_values_to_be_in_set"]

    def test_no_duplicate_chunks(self, fhir_kb):
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_no_dupes",
            [gx.expectations.ExpectCompoundColumnsToBeUnique(
                column_list=["resource", "content"]
            )])
        assert results["expect_compound_columns_to_be_unique"]

    def test_all_targeted_resources_are_present(self, fhir_kb):
        _, loaded_resources, _ = fhir_kb
        missing = loaded_resources - ALL_FHIR_RESOURCES
        assert len(missing) == 0, f"Missing resources in KB: {sorted(missing)}"