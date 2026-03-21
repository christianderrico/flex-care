# flex-care

FLEX-CARE is a modular LLMOps pipeline for automatic FHIR resource mapping.
Given a natural language description of a clinical dataset column, the system
returns an ordered set of candidate HL7 FHIR R4 resources, combining an
instruction-tuned Large Language Model with a Retrieval-Augmented Generation
(RAG) mechanism built on top of the official FHIR documentation.

The pipeline is designed following the **4D LLMOps framework**
(Discover → Distill → Deploy → Deliver) and integrates MLflow for
experiment tracking, DVC for data versioning, and pylint for code quality.

---

## Repository structure
```
├── data
│   ├── external            <- Data from third party sources.
│   ├── interim             <- Intermediate data that has been transformed.
│   ├── processed           <- Final datasets for evaluation.
│   ├── raw                 <- Original, immutable data dump.
│   └── FHIR_resources.csv  <- List of targeted FHIR R4 resources.
├── docs                    <- Project documentation.
├── notebooks               <- Jupyter notebooks for inference and analysis.
├── references
│   └── configs
│       ├── config.yaml     <- Main pipeline configuration file.
│       └── prompts/        <- Prompt templates for the classifier.
├── src
│   ├── data
│   │   ├── loader.py       <- Loads FHIR docs and evaluation datasets.
│   │   ├── scraper.py      <- Scrapes HL7 FHIR R4 documentation.
│   │   └── resources.py    <- Loads and filters targeted FHIR resources.
│   ├── features
│   │   └── vectorstore.py  <- FAISS-based vector store for retrieval.
│   ├── models
│   │   └── classifier.py   <- LLM classifier with constrained decoding.
│   └── evaluation
│       ├── metrics.py      <- Classification and retrieval metrics.
│       └── logging.py      <- MLflow logging utilities.
├── test                    <- Unit tests.
├── .dvc/                   <- DVC configuration.
├── .pylintrc               <- Pylint configuration.
├── Makefile                <- Utility commands.
├── pyproject.toml          <- Project metadata.
└── requirements.txt        <- Python dependencies.
```

---

## Pipeline overview

The system addresses FHIR resource mapping as a **multi-class classification
task**: given a free-text description `d` of a dataset column, it returns an
ordered set of candidate FHIR resources `R = {r1, ..., rk}`.

The pipeline consists of four components:

1. **Loader** — loads the scraped FHIR documentation and the evaluation
   dataset from CSV, normalising mappings to root resource names.
2. **VectorStore** — chunks the FHIR documentation, encodes it with a
   biomedical sentence embedding model, and builds a FAISS index for
   cosine similarity retrieval.
3. **Classifier** — wraps an instruction-tuned causal LM and uses
   constrained decoding via [Outlines](https://github.com/outlines-dev/outlines)
   to guarantee structured JSON output. The model selects `k` candidates
   from the retrieved context.
4. **Evaluation** — computes accuracy, precision, recall, F1, and hit@k,
   logging all metrics and prediction artifacts to MLflow.

---

## Datasets

The pipeline is evaluated on three clinical datasets:

| Dataset | Domain | Variables | FHIR resources |
|---|---|---|---|
| MOTU | Rehabilitation (trans-femoral amputation) | 157 | 18 |
| MIMIC-IV | Critical care (ICU, ED, EHR) | — | 25 profiles |
| SPHN | Swiss federated clinical data (semantic framework) | — | 22 |

---

## Configuration

All pipeline parameters are controlled by a single YAML file:
```yaml
project_name: "FHIR Classification"

dataset:
  name: "motu_enriched.csv"

retrieval:
  embeddings: "abhinand/MedEmbed-large-v0.1"
  k: 6
  every_represented_candidate: true
  chunk_size: 6
  index_path: "models/faiss_index"

model:
  name: "prithivMLmods/Qwen-UMLS-7B-Instruct"
  n_output: 3
  prompt_template: "references/configs/prompts/prompt_top_3.txt"
```

---

## Setup
```bash
# clone the repository
git clone https://github.com/christianderrico/flex-care.git
cd flex-care

# create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# configure environment variables
cp .env.example .env
# set HF_KEY=<your_huggingface_token> in .env
```

---

## Regenerating the FHIR knowledge base

The scraped FHIR documentation is not versioned in this repository.
To regenerate it:
```python
from src.data.scraper import scrape_all_resources
from pathlib import Path

scrape_all_resources(
    resources_path=Path("data/FHIR_resources.csv"),
    docs_dir=Path("data/Docs")
)
```

---

## Running an experiment
```bash
# start MLflow tracking server
mlflow server --host 127.0.0.1 --port 8080

# run inference and evaluation
jupyter nbconvert --to notebook --execute notebooks/inference.ipynb
```

Results are logged to MLflow at `http://localhost:8080`.

---

## Code quality
```bash
# run pylint on the source modules
python -m pylint src/
```

Current pylint score: **9.94/10**.

---

## Data versioning

Large files (FHIR docs, FAISS index) are versioned with DVC:
```bash
dvc pull   # download data from remote storage
dvc push   # upload data to remote storage
```

---

## References

- Lanubile et al., *Teaching MLOps in Higher Education through
  Project-Based Learning*, ICSE-SEET 2023.
- HL7 FHIR R4 — https://hl7.org/fhir/R4
- [MLflow](https://mlflow.org) — experiment tracking
- [DVC](https://dvc.org) — data version control
- [Outlines](https://github.com/outlines-dev/outlines) — structured
  generation
- [FAISS](https://github.com/facebookresearch/faiss) — vector similarity
  search
