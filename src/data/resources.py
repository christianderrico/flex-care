"""Utilities for loading and filtering the targeted FHIR resource list."""

from pathlib import Path
import pandas as pd

def __parse_maturity(value) -> int:
    unknown_maturity  = 5
    return int(value) if str(value).isdigit() else unknown_maturity

def load_resources(path: Path, sep: str = ",") -> list[str]:
    """Sorted, deduplicated list of targeted FHIR resource names."""
    df = pd.read_csv(path, sep=sep)
    df["MaturityLevel"] = df["MaturityLevel"].map(__parse_maturity)

    valid_groups = frozenset({"Clinical", "Base", "Specialized"})

    mask = (
        df["GroupName"].isin(valid_groups) &
        df["MaturityLevel"].ne(0) &
        df["Resource"].notna()
    )
    return sorted({
        r.strip().lower()
        for r in df.loc[mask, "Resource"]
        if r.strip()
    })
