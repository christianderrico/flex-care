"""MLflow logging utilities for experiment tracking."""

import mlflow
import pandas as pd

from src.models.classifier import PredictionResult


def log_predictions_as_artifact(results: list[PredictionResult], dataset: list[dict]) -> None:
    """
    Log prediction results as a tabular MLflow artifact.

    Builds a row per sample containing the input description, retrieved
    FHIR resource candidates, model prediction, ground truth, and a
    correctness flag, then logs the resulting table to the active MLflow run.

    Parameters
    ----------
    results : list[PredictionResult]
        Prediction results as returned by ``Classifier.predict``.
    dataset : list[dict]
        Original dataset samples, each containing a ``text`` field with
        the input column description.
    """
    rows = []
    for i, (r, item) in enumerate(zip(results, dataset)):

        rows.append({
            "sample_id":           i,
            "description":         item['text'],
            "retrieved_resources": ", ".join(r.retrieved_resources),
            "y_pred":              r.y_pred,
            "y_true":              r.y_true,
            "correct":             r.y_pred == r.y_true,
            "answer":              str(", ".join([answer for _, answer in r.answer]))
        })

    df = pd.DataFrame(rows)

    mlflow.log_table(data=df, artifact_file="predictions.json")


def log_configuration(cfg: dict):
    """
    Log a nested configuration dictionary as MLflow parameters.

    Flattens the configuration using dot-separated keys before logging,
    so nested fields like ``model.name`` are logged as a single parameter.

    Parameters
    ----------
    cfg : dict
        Pipeline configuration as loaded from the YAML config file.
    """
    flat = pd.json_normalize(cfg, sep=".").to_dict(orient="records")[0]
    mlflow.log_params(flat)
