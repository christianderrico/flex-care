"""
Data quality validation for the FHIR RAG mapping pipeline.
"""

import ast
import json
from pathlib import Path

import great_expectations as gx
import pandas as pd
import pytest

DATASETS = {
    "MOTU":     Path("data/motu/motu.csv"),
    "MIMIC-IV": Path("data/mimic/mimic.csv"),
    "SPHN":     Path("data/sphn/sphn.csv"),
}

FHIR_KB_DIR = Path("data/Docs")

ALL_FHIR_RESOURCES: set[str] = set(
    pd.read_csv(Path("data/FHIR_resources.csv"))["Resource"]
    .dropna()
    .str.lower()
    .unique()
)
"""Lowercased set of every valid FHIR resource name, loaded once at import time."""

MIN_DESCRIPTION_LENGTH = 1   # Minimum non-empty field description (characters)
MIN_CHUNK_LENGTH = 20        # Minimum KB content chunk length (characters)

def _make_batch(df: pd.DataFrame, source_name: str) -> tuple:
    """
    Register a DataFrame as an ephemeral GX data source and return a
    ready-to-validate (batch, context) pair.

    Args:
        df: The DataFrame to wrap.
        source_name: A unique identifier used to name the data source,
            asset, and batch definition within the GX context.

    Returns:
        A (batch, context) tuple where ``batch`` can be passed directly
        to ``batch.validate(suite)``.
    """
    context = gx.get_context()
    data_source = context.data_sources.add_pandas(name=source_name)
    data_asset = data_source.add_dataframe_asset(name=f"{source_name}_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe(
        f"{source_name}_batch"
    )
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
    return batch, context


def _run_suite(
    df: pd.DataFrame,
    source_name: str,
    suite_name: str,
    expectations: list,
) -> dict[str, bool]:
    """
    Build a GX expectation suite, validate the given DataFrame, and return
    per-expectation results.

    Args:
        df: DataFrame to validate.
        source_name: Unique name for the GX data source (passed to
            :func:`_make_batch`).
        suite_name: Name for the new :class:`gx.ExpectationSuite`.
        expectations: List of GX expectation objects to add to the suite.

    Returns:
        Mapping of ``expectation_type`` strings (e.g.
        ``"expect_column_to_exist"``) to boolean success flags.
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
    """
    Return ``True`` if *value* contains at least one root FHIR resource name
    that exists in :data:`ALL_FHIR_RESOURCES`.

    Handles two formats:
    - A plain string such as ``"Observation.code"``
    - A Python-literal list such as ``"['Observation.code', 'Patient.id']"``

    Args:
        value: Raw mapping string from a dataset row.

    Returns:
        ``True`` when at least one root resource is valid; ``False`` on any
        parse error or when no valid resource root is found.
    """
    try:
        raw = ast.literal_eval(value) if str(value).strip().startswith("[") else [value]
        roots = {m.split(".")[0].lower() for m in raw}
        return bool(roots & ALL_FHIR_RESOURCES)
    except ValueError:
        return False


def _extract_content(item: object) -> str:
    """
    Coerce a list element to a string content value.

    Args:
        item: A list element from a parsed FHIR JSON value — either a
            plain string or a JSON-serialisable object.

    Returns:
        The item itself if it is already a string, otherwise its
        JSON-serialised representation.
    """
    return item if isinstance(item, str) else json.dumps(item)


def _records_from_file(fp: Path) -> list[dict]:
    """
    Parse a single FHIR JSON file and return a flat list of content records.

    Each record is a dict with the keys:
    - ``"resource"``: lowercased file stem (e.g. ``"observation"``).
    - ``"content"``: a non-empty string extracted from the JSON value.

    String values are included as-is; list values are expanded so that
    each element becomes its own record (non-string elements are
    JSON-serialised via :func:`_extract_content`). The top-level key
    ``"resource"`` is skipped to avoid self-referential duplication.

    Args:
        fp: Path to a ``.json`` file inside :data:`FHIR_KB_DIR`.

    Returns:
        List of ``{"resource": ..., "content": ...}`` dicts (may be empty
        if the file contains no usable string content).
    """
    resource_name = fp.stem.lower()
    raw = json.loads(fp.read_text(encoding="utf-8"))
    records = []

    for key, value in raw.items():
        if key == "resource":
            continue
        if isinstance(value, str) and value.strip():
            records.append({"resource": resource_name, "content": value})
        elif isinstance(value, list):
            for item in value:
                content = _extract_content(item)
                if content.strip():
                    records.append({"resource": resource_name, "content": content})

    return records


def _load_eval_batch(path: Path, name: str) -> tuple[pd.DataFrame, str]:
    """
    Load a CSV eval dataset and return it together with its logical name.

    Args:
        path: Filesystem path to the CSV file.
        name: Short identifier used as the GX source name in test suites.

    Returns:
        A ``(DataFrame, name)`` tuple.
    """
    return pd.read_csv(path), name

@pytest.fixture(name="motu")
def motu_fixture() -> tuple[pd.DataFrame, str]:
    """Pytest fixture: loads the MOTU eval dataset."""
    return _load_eval_batch(DATASETS["MOTU"], "motu")


@pytest.fixture(name="mimic")
def mimic_fixture() -> tuple[pd.DataFrame, str]:
    """Pytest fixture: loads the MIMIC-IV eval dataset."""
    return _load_eval_batch(DATASETS["MIMIC-IV"], "mimic")


@pytest.fixture(name="sphn")
def sphn_fixture() -> tuple[pd.DataFrame, str]:
    """Pytest fixture: loads the SPHN eval dataset."""
    return _load_eval_batch(DATASETS["SPHN"], "sphn")


@pytest.fixture(name="fhir_kb")
def fhir_kb_fixture() -> tuple[pd.DataFrame, set[str], str]:
    """
    Pytest fixture: scan :data:`FHIR_KB_DIR`, parse every JSON file, and
    return a flat DataFrame of content records alongside metadata.

    Returns:
        A three-tuple ``(df, loaded_resources, source_name)`` where:

        - ``df`` — DataFrame with columns ``resource`` and ``content``,
          one row per extracted string chunk.
        - ``loaded_resources`` — set of lowercased resource names for all
          JSON files found in the KB directory.
        - ``source_name`` — fixed string ``"fhir_kb"`` for use as the GX
          source identifier.
    """
    all_json_files = [
        fp
        for resource_dir in FHIR_KB_DIR.iterdir()
        if resource_dir.is_dir()
        for fp in resource_dir.glob("*.json")
    ]
    records = [
        record
        for fp in all_json_files
        for record in _records_from_file(fp)
    ]
    loaded_resources = {fp.stem.lower() for fp in all_json_files}
    return pd.DataFrame(records), loaded_resources, "fhir_kb"


@pytest.fixture(name="eval_fixture", params=["motu", "mimic", "sphn"])
def eval_fixture_factory(
    request,
    motu: tuple[pd.DataFrame, str],
    mimic: tuple[pd.DataFrame, str],
    sphn: tuple[pd.DataFrame, str],
) -> tuple[pd.DataFrame, str]:
    """
    Parametrised fixture that iterates over all three eval datasets.

    Yields each of ``motu``, ``mimic``, and ``sphn`` in turn so that
    every test in :class:`TestEvalDatasetQuality` runs against all datasets
    without repetition.
    """
    return {"motu": motu, "mimic": mimic, "sphn": sphn}[request.param]

class TestEvalDatasetQuality:
    """Structural and content-quality checks for the three eval datasets."""

    def test_field_description_column_exists(self, eval_fixture):
        """The ``Field_description`` column must be present."""
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_col_exists",
            [gx.expectations.ExpectColumnToExist(column="Field_description")])
        assert results["expect_column_to_exist"]

    def test_mapping_column_exists(self, eval_fixture):
        """The ``Mapping`` column must be present."""
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_mapping_exists",
            [gx.expectations.ExpectColumnToExist(column="Mapping")])
        assert results["expect_column_to_exist"]

    def test_no_null_field_descriptions(self, eval_fixture):
        """No row may have a null ``Field_description``."""
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_no_null_desc",
            [gx.expectations.ExpectColumnValuesToNotBeNull(column="Field_description")])
        assert results["expect_column_values_to_not_be_null"]

    def test_no_null_mappings(self, eval_fixture):
        """No row may have a null ``Mapping``."""
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_no_null_map",
            [gx.expectations.ExpectColumnValuesToNotBeNull(column="Mapping")])
        assert results["expect_column_values_to_not_be_null"]

    def test_description_min_length(self, eval_fixture):
        """Every ``Field_description`` must meet :data:`MIN_DESCRIPTION_LENGTH`."""
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_desc_length",
            [gx.expectations.ExpectColumnValueLengthsToBeBetween(
                column="Field_description", min_value=MIN_DESCRIPTION_LENGTH
            )])
        assert results["expect_column_value_lengths_to_be_between"]

    def test_no_duplicate_rows(self, eval_fixture):
        """The combination of all columns must be unique across every row."""
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_no_dupes",
            [gx.expectations.ExpectCompoundColumnsToBeUnique(
                column_list=list(df.columns)
            )])
        assert results["expect_compound_columns_to_be_unique"]

    def test_dataset_is_not_empty(self, eval_fixture):
        """The dataset must contain at least one row."""
        df, name = eval_fixture
        results = _run_suite(df, name, "suite_not_empty",
            [gx.expectations.ExpectTableRowCountToBeBetween(min_value=1)])
        assert results["expect_table_row_count_to_be_between"]

    def test_all_mappings_are_valid_fhir_resources(self, eval_fixture):
        """Every ``Mapping`` value must reference at least one valid FHIR resource root."""
        df, _ = eval_fixture
        invalid = df["Mapping"].apply(lambda v: not _mapping_is_valid(str(v))).sum()
        assert invalid == 0, (
            f"{invalid} rows have mappings outside the valid FHIR resource set"
        )

class TestFHIRKnowledgeBaseQuality:
    """Content and coverage checks for the scraped FHIR knowledge base."""

    def test_kb_is_not_empty(self, fhir_kb):
        """At least one content chunk must be loaded from the KB directory."""
        df, _, _ = fhir_kb
        assert len(df) > 0, "No chunks found in the FHIR knowledge base directory"

    def test_no_null_resource_identifiers(self, fhir_kb):
        """No chunk may have a null ``resource`` identifier."""
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_no_null_resource",
            [gx.expectations.ExpectColumnValuesToNotBeNull(column="resource")])
        assert results["expect_column_values_to_not_be_null"]

    def test_no_null_content(self, fhir_kb):
        """No chunk may have null ``content``."""
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_no_null_content",
            [gx.expectations.ExpectColumnValuesToNotBeNull(column="content")])
        assert results["expect_column_values_to_not_be_null"]

    def test_chunk_min_length(self, fhir_kb):
        """Every content chunk must be at least :data:`MIN_CHUNK_LENGTH` characters."""
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_chunk_length",
            [gx.expectations.ExpectColumnValueLengthsToBeBetween(
                column="content", min_value=MIN_CHUNK_LENGTH
            )])
        assert results["expect_column_value_lengths_to_be_between"]

    def test_all_resource_names_are_valid(self, fhir_kb):
        """Every ``resource`` value must belong to :data:`ALL_FHIR_RESOURCES`."""
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_valid_resources",
            [gx.expectations.ExpectColumnValuesToBeInSet(
                column="resource", value_set=ALL_FHIR_RESOURCES
            )])
        assert results["expect_column_values_to_be_in_set"]

    def test_no_duplicate_chunks(self, fhir_kb):
        """The ``(resource, content)`` pair must be unique across all chunks."""
        df, _, name = fhir_kb
        results = _run_suite(df, name, "suite_kb_no_dupes",
            [gx.expectations.ExpectCompoundColumnsToBeUnique(
                column_list=["resource", "content"]
            )])
        assert results["expect_compound_columns_to_be_unique"]

    def test_all_targeted_resources_are_present(self, fhir_kb):
        """Every resource found in the KB directory must map to a known FHIR resource."""
        _, loaded_resources, _ = fhir_kb
        missing = loaded_resources - ALL_FHIR_RESOURCES
        assert len(missing) == 0, f"Missing resources in KB: {sorted(missing)}"
