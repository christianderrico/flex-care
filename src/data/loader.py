"""
Loader module for FHIR documentation and clinical dataset ingestion.
"""

import ast
import json
from pathlib import Path
import pandas as pd
from src.data.resources import load_resources

class Loader:
    """
    Loads data from disk: resources, documents, and datasets.

    Responsibilities:
    - Read the resource list from the CSV
    - Load scraped JSON documents from the Docs directory
    - Load and filter raw mapping datasets

    Out of scope (handled elsewhere):
    - Scraping  → scraper.py
    - Chunking  → vectorstore.py

    Parameters
    ----------
    docs_path : Path
        Root directory containing scraped resource JSON files.
    dataset_dir : Path
        Directory containing raw dataset CSV files.
    resources_list_path : Path
        Path to the CSV file listing FHIR resources.
    sep : str, optional
        CSV column separator, by default ``","``.
    """

    _EXCLUDED_SECTIONS = frozenset({"introduction", "Scope and Usage", "title"})
    _INTRO_CUTOFF      = "This resource is referenced"
    _ROOT = Path(__file__).resolve().parents[2]

    def __init__(
        self,
        docs_path      = _ROOT / "data" / "Docs",
        dataset_path   = _ROOT / "data",
        resources_path = _ROOT / "data" / "FHIR_resources.csv"
    ):
        self.__docs_path:            Path = docs_path
        self.__dataset_dir:          Path = dataset_path
        self.__resources_list_path:  Path = resources_path
        self.__resources:       list[str] = load_resources(self.__resources_list_path)
        self.__documents:       list[str] = self.__load_docs()

    @staticmethod
    def __parse_mapping(value: str) -> list[str]:
        raw = ast.literal_eval(value) if value.startswith("[") else [value]
        return list({m.split(".")[0].lower() for m in raw})

    @staticmethod
    def __parse_documentation(documentation: dict[str, str]) -> list[str]:
        return [
            f"{'.'.join(k.split('.')[1:])}: {v}" if "." in k else f"{k}: {v}"
            for k, v in documentation.items()
        ]

    @staticmethod
    def __parse_examples(examples: list[dict], resource: str) -> list[str]:
        return [f"{e['name']} is an example of {resource}" for e in examples]

    def __parse_sections(self, sections: dict) -> dict[str, str]:
        intro = sections.get("introduction", "").split(self._INTRO_CUTOFF)[0].strip()
        usage = sections.get("Scope and Usage", "")
        extra = "\n".join(v for k, v in sections.items() if k not in self._EXCLUDED_SECTIONS)
        return {"description": intro, "usage": usage, "extra": extra}

    def __build_resource_document(self, doc: dict, resource: str) -> str:
        return json.dumps({
            "resource":      resource,
            **self.__parse_sections(doc["sections"]),
            "examples":      self.__parse_examples(doc.get("examples", []), resource),
            "documentation": self.__parse_documentation(doc.get("documentation", {})),
        })

    def __filter_by_resources(self, df: pd.DataFrame) -> pd.DataFrame:
        def matches(value: str) -> bool:
            mappings = ast.literal_eval(value) if value.strip().startswith("[") else [value]
            roots = {m.split(".")[0].lower() for m in mappings}
            return bool(roots & set(self.__resources))

        return df.loc[df["Mapping"].apply(matches)]

    def __load_docs(self):
        if not any(self.__docs_path.glob("*/*.json")):
            raise RuntimeError(
                f"No documents found in {self.__docs_path}. "
                "Run scrape_all_resources() first."
            )
        return [
            self.__build_resource_document(
                doc      = json.loads(fp.read_text(encoding="utf-8")),
                resource = fp.stem,
            )
            for fp in sorted(self.__docs_path.glob("*/*.json"))
        ]


    @property
    def docs(self) -> list[str]:
        """
        Serialised resource points loaded from ``docs_path``.

        Returns
        -------
        list[str]
            One JSON string per resource, ready to be ingested by the vectorstore.

        Raises
        ------
        RuntimeError
            If no scraped documents are found. Run ``scrape_all_resources()`` first.
        """

        return list(self.__documents)

    def load_dataset(self, name: str) -> list[dict]:
        """
        Load and normalise a mapping dataset.

        Parameters
        ----------
        name : str
            CSV filename inside ``dataset_dir``
            (e.g. ``"sphn copy.csv"``, ``"mimic.csv"``).

        Returns
        -------
        list[dict]
            Each dict has:

            - ``text`` (str): Input field description.
            - ``ground_truth`` (list[str]): Deduplicated lowercase resource names.

        Raises
        ------
        FileNotFoundError
            If the CSV file does not exist at the expected path.
        """
        df = pd.read_csv(self.__dataset_dir / name)[["Field_description", "Mapping"]].rename(
            columns={"Field_description": "text"}
        )
        df = self.__filter_by_resources(df)

        return [
            {
                "text":         row["text"],
                "ground_truth": self.__parse_mapping(str(row["Mapping"])),
            }
            for _, row in df.iterrows()
        ]
