# flex-care

FLEX-LLM-CARE is a modular LLM-based transformation framework designed to standardize unstructured clinical data into structured FHIR (Fast Healthcare Interoperability Resources) formats. This system empowers scalable automation and reasoning across clinical NLP pipelines, bridging the gap between language models and healthcare standards.

## Repository structure

```text
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
├── docs               <- Directory for documentation.
├── example            <- Directory for test scripts and src.
├── models             <- Trained and serialized models, model predictions, or model summaries.
├── notebooks          <- Directory with Jupyter notebooks.
├── references         <- Directory containing project references.
├── reports            <- Generated HTML, PDF, LaTeX, etc. reports.
│   └── figures        <- Graphs and figures generated to use in reports.
├── src                <- Project source code.
│   ├── data           <- Scripts to download or generate data.
│   ├── features       <- Scripts to turn raw data into features.
│   ├── models         <- Scripts to train and use models.
│   └── visualization  <- Scripts to create visualizations.
├── test               <- Project test code.
│   ├── data
│   ├── features
│   ├── models
│   └── visualization
├── Makefile           <- Makefile with `make install_requirements` command.
├── README.md          <- Project markdown file created.
├── requirements.txt   <- Txt file containing all requirements to install in venv.
├── setup.sh           <- Allows you to configure git and DVC.
```
# flex-care
