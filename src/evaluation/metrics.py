"""
Evaluation metrics for FHIR resource classification.
"""

from sklearn.metrics import precision_score, recall_score, accuracy_score, f1_score
from evaluation.rag_metrics import hit_k
from src.models.classifier import PredictionResult

def evaluate(results: list[PredictionResult]) -> dict[str, float]:
    """
    Compute classification metrics for FHIR resource predictions.

    Parameters
    ----------
    results : list[PredictionResult]
        List of prediction results, each containing the model's predicted
        FHIR resource(s), the ground-truth resource, and the retrieved
        candidate contexts.

    Returns
    -------
    dict[str, float]
        Dictionary containing the following metrics:

        - ``accuracy``           : exact-match accuracy over all samples.
        - ``precision_macro``    : macro-averaged precision.
        - ``precision_weighted`` : weighted-averaged precision.
        - ``recall_macro``       : macro-averaged recall.
        - ``recall_weighted``    : weighted-averaged recall.
        - ``hit_rate_k``         : hit-rate@k, i.e. fraction of samples where
                                   the ground-truth resource appears among the
                                   top-k retrieved candidates.
        - ``f1_score``           :
    """
    actuals = [r.y_true for r in results]
    predictions = [r.y_pred for r in results]
    contexts = [r.retrieved_resources for r in results]

    kwargs = {"y_true": actuals, "y_pred": predictions, "zero_division": 0}

    return {
        "accuracy":           accuracy_score(actuals, predictions),
        "precision_macro":    precision_score(**kwargs, average="macro"),
        "precision_weighted": precision_score(**kwargs, average="weighted"),
        "recall_macro":       recall_score(**kwargs, average="macro"),
        "recall_weighted":    recall_score(**kwargs, average="weighted"),
        "f1_score":           f1_score(**kwargs, average="weighted"),
        "hit_Rate_k":         hit_k(contexts, actuals)
    }
