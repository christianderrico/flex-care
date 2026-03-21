""" import json
import pytest
import pandas as pd
from src.models.rag.retriever import FaissRetriever
from src.models.rag.loaders import load_db, load_embeddings, load_documentation, load_resources


@pytest.fixture(scope="module")
def retriever():
    embeddings = load_embeddings("abhinand/MedEmbed-large-v0.1")
    csv_path = "data/FHIR_resources.csv"
    docs_dir = "data/Docs"
    documents = load_documentation(docs_dir, csv_path)
    index = load_db(embeddings, documents)
    return FaissRetriever(index, embeddings, documents)


@pytest.fixture(scope="module")
def eval_data():
    sphn = pd.read_csv("data/sphn copy.csv")
    resources = load_resources("data/FHIR_resources.csv")
    sphn = sphn.loc[
    sphn["Mapping"]
        .str.split(".", n=1).str[0]   
        .str.lower()                  
        .isin(resources)             
    ]
    return sphn

def test_recall_at_5(retriever, eval_data):
    correct = 0
    total = len(eval_data)

    for _, example in eval_data.iterrows():
        query = example["Field_description"]
        expected = example["Mapping"].split(".")[0].lower()

        result = retriever.retrieve(query, n=10, every_represented_candidate=False)

        retrieved_types = result['resources']
        print("Expected: ", expected)
        print(retrieved_types)

        if expected in retrieved_types:
            correct += 1

    recall = correct / total
    
    print("AAAAAAAAAAAAAAAAAAAAAAAA")

    print(f"\nRecall@5: {recall:.2f}")

    assert recall == 1.0 """