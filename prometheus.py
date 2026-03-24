import time
import mlflow
import pandas as pd
from prometheus_client import start_http_server, Gauge
from mlflow.tracking import MlflowClient

print(mlflow.get_tracking_uri())
mlflow.set_tracking_uri("http://localhost:8080")

accuracy  = Gauge('mlflow_accuracy',  'Accuracy del run', ['run_id', 'experiment', 'status'])
loss      = Gauge('mlflow_loss',      'Loss del run',     ['run_id', 'experiment', 'status'])
run_count = Gauge('mlflow_run_count', 'Numero totale di run', ['experiment'])

def update_metrics():
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
                "run_id":     run.info.run_id[:8],
                "experiment": exp.name,
                "status":     run.info.status
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
    # start_http_server(8001)
    # while True:
    #     update_metrics()
    #     time.sleep(15)