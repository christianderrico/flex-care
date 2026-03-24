"""
MLflow to Prometheus metrics exporter.
"""

import mlflow
from prometheus_client import Gauge
from mlflow.tracking import MlflowClient

print(mlflow.get_tracking_uri())
mlflow.set_tracking_uri("http://localhost:8080")

accuracy = Gauge(
    "mlflow_accuracy",
    "Accuracy del run",
    ["run_id", "experiment", "status"]
)
"""Prometheus Gauge tracking the accuracy metric for each MLflow run."""

loss = Gauge(
    "mlflow_loss",
    "Loss del run",
    ["run_id", "experiment", "status"]
)
"""Prometheus Gauge tracking the loss metric for each MLflow run."""

run_count = Gauge(
    "mlflow_run_count",
    "Numero totale di run",
    ["experiment"]
)
"""Prometheus Gauge tracking the total number of runs per experiment."""


def update_metrics() -> None:
    """Scrape MLflow experiments and export run metrics to Prometheus.

    Connects to the MLflow tracking server, iterates over all available
    experiments, and updates the Prometheus Gauges for each run that
    exposes an ``accuracy`` or ``loss`` metric. Also updates the total
    run count per experiment.

    The function queries up to 100 runs per experiment. Runs missing
    a given metric are silently skipped for that metric only.

    Side effects:
        Updates the global Prometheus Gauges ``accuracy``, ``loss``,
        and ``run_count`` with the latest values from the MLflow server.

    Example::

        update_metrics()
        # Gauges are now populated and ready to be scraped by Prometheus.
    """
    print("Cerco esperimenti...")
    client = MlflowClient()

    experiments = client.search_experiments()
    print(f"Trovati {len(experiments)} esperimenti")

    for exp in experiments:
        runs = client.search_runs(
            experiment_ids=[exp.experiment_id],
            max_results=100
        )
        print(f"Esperimento {exp.name}: {len(runs)} run")
        run_count.labels(experiment=exp.name).set(len(runs))

        for run in runs:
            labels = {
                "run_id": run.info.run_id[:8],
                "experiment": exp.name,
                "status": run.info.status,
            }
            metrics = run.data.metrics
            if "accuracy" in metrics:
                accuracy.labels(**labels).set(metrics["accuracy"])
                print(f"  accuracy: {metrics['accuracy']}")
            if "loss" in metrics:
                loss.labels(**labels).set(metrics["loss"])
                print(f"  loss: {metrics['loss']}")


if __name__ == "__main__":
    update_metrics()
    # Uncomment the block below to enable continuous monitoring mode.
    # Starts a Prometheus HTTP server on port 8001 and refreshes
    # metrics every 15 seconds, keeping Grafana dashboards live.
    #
    # from prometheus_client import start_http_server
    # import time
    # start_http_server(8001)
    # while True:
    #     update_metrics()
    #     time.sleep(15)
