"""
Instruction-tuned LLM classifier for FHIR resource mapping.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from outlines.types import JsonSchema
import outlines
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import logging as hf_logging

from src.features.vectorstore import VectorStore


@dataclass
class PredictionResult:
    """
    Dataclass holding a single FHIR resource classification result.

    Attributes
    ----------
    question : str
        Full instantiated prompt sent to the model, including context
        and input description.
    contexts : list[str]
        Raw context chunks retrieved from the vector store, one per
        retrieved candidate.
    retrieved_resources : list[str]
        Ordered list of FHIR resource names returned by the retriever,
        in the same order as ``contexts``.
    answer : list[str]
        Raw model output as a list of (letter, resource) tuples,
        where the letter corresponds to the labelled candidate in
        the context and the resource is the resolved resource name.
    y_pred : str
        Final predicted FHIR resource name selected by the classifier.
    y_true : str
        Ground-truth FHIR resource name for the sample.
    """
    question:            str                   = ""
    contexts:            list[str]             = field(default_factory=list)
    retrieved_resources: list[str]             = field(default_factory=list)
    answer:              list[str]             = field(default_factory=list)
    y_pred:              list[tuple[str, str]] = field(default_factory=list)
    y_true:              str                   = ""

class Classifier:
    """
    Loads a causal LM and runs structured FHIR resource classification inference
    using constrained decoding via Outlines to guarantee valid JSON output.

    Parameters
    ----------
    name : str
        HuggingFace model identifier or local path (e.g. ``"meta-llama/Llama-3.2-1B"``).
    n_output : int
        Number of FHIR resource candidates to return per sample.
        Controls the exact cardinality of the model output array.
    prompt_template : str | Path | None, optional
        Prompt template used to format each inference request.

        - ``None``      → raises ``KeyError`` at initialisation time.
        - ``Path``      → template is read from the given file path.
        - ``str``       → used directly as the template string.

        The template **must** expose two placeholders:

        - ``{context}``     – ranked FHIR resource candidates from the vector store.
        - ``{description}`` – free-text clinical description to classify.

    cache_dir : str, optional
        Local directory for caching HuggingFace model weights.
        Defaults to ``"/mnt/data_ml/hf_cache"``.

    Raises
    ------
    KeyError
        If ``prompt_template`` is ``None``.

    """

    def __init__(
        self,
        name:            str,
        n_output:        int,
        prompt_template: str | Path | None = None,
        cache_dir:       str = "/mnt/data_ml/hf_cache"
    ):
        self.__prompt_template = self.__load_prompt(prompt_template)

        hf_logging.set_verbosity_error()
        tokenizer          = self.__load_tokenizer(name, cache_dir)
        hf_model           = self.__load_model(name, cache_dir, tokenizer.eos_token_id)
        self.__output_type = self.__load_json_schema(n_output)
        self.__generator   = outlines.from_transformers(
            model                  = hf_model,
            tokenizer_or_processor = tokenizer,
        )

    @staticmethod
    def __load_json_schema(top_k: int):
        return JsonSchema({
            "type": "object",
            "properties": {
                "answer": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^[A-Z]$"},
                    "minItems": top_k,
                    "maxItems": top_k
                }
            },
            "required": ["answer"]
        })

    @staticmethod
    def __load_tokenizer(name: str, cache_dir: str) -> AutoTokenizer:
        tokenizer           = AutoTokenizer.from_pretrained(name, cache_dir=cache_dir)
        tokenizer.pad_token = tokenizer.eos_token
        return tokenizer

    @staticmethod
    def __load_model(
        name:         str,
        cache_dir:    str,
        pad_token_id: int,
    ) -> AutoModelForCausalLM:
        model                     = AutoModelForCausalLM.from_pretrained(
            name,
            cache_dir=cache_dir,
            dtype="auto",
            device_map="auto",
        )
        model.config.pad_token_id = pad_token_id
        return model

    @staticmethod
    def __load_prompt(source: str | Path | None) -> str:
        if source is None:
            raise KeyError("Missing 'path' in configuration file")
        path = Path(source)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return source

    def __build_prompt(self, context: str, description: str) -> str:
        return (
            self.__prompt_template
            .replace("{context}", context)
            .replace("{description}", description)
        )

    @staticmethod
    def __parse_predictions(context: str, generated: dict) -> list[tuple[str, str]]:
        def parse_y_pred(context: str, letter: str) -> str | None:
            for line in context.split("\n"):
                if line.startswith(f"{letter})"):
                    parts = line.split(") ", 1)
                    if len(parts) > 1:
                        return parts[1].split(": ")[0].lower()
            return None

        return [
            (letter, pred)
            if (pred := parse_y_pred(context, letter.upper())) is not None
            else ('', '')
            for letter in generated["answer"]
        ]

    @staticmethod
    def __split_context_documents(context: str) -> list[str]:
        return re.split(r"(?m)^[A-Z]+\)\s*", context)[1:]

    @staticmethod
    def __get_retrieved_resources(contexts: list[str]) -> list[str]:
        return [row.split(":")[0] for row in contexts]

    @staticmethod
    def __filter_items(y_preds: list[str], ground_truth: list[str]) -> tuple[str, str]:
        predicted = next((p for p in y_preds if p in ground_truth), y_preds[0])
        y_true    = next((g for g in ground_truth if g in y_preds), ground_truth[0])
        return predicted, y_true

    def predict(
        self,
        vs:                          VectorStore,
        dataset:                     list[dict],
        k:                           int  = 10,
        every_represented_candidate: bool = False,
    ) -> list[PredictionResult]:
        """
        Run inference over a dataset and return structured results.

        Parameters
        ----------
        vs : VectorStore
            Vector store used to retrieve the top-k FHIR resource candidates
            for each sample.
        dataset : list[dict]
            List of samples to classify. Each dict must contain:

            - ``text``         – free-text clinical description to classify.
            - ``ground_truth`` – list of valid FHIR resource names for the sample.

            As returned by ``Loader.load_dataset``.
        k : int, optional
            Number of candidate resources to retrieve from the vector store
            per sample, by default ``10``.
        every_represented_candidate : bool, optional
            If ``True``, deduplicate retrieved candidates by resource type
            before building the context, by default ``False``.

        Returns
        -------
        list[y_predResult]
            One :class:`y_predResult` per sample in ``dataset``.
            If inference fails for a sample, an empty :class:`y_predResult`
            with only ``question`` populated is appended and a warning is printed.
        """
        results = []

        for item in tqdm(dataset, desc="Predicting"):
            try:
                ctx       = vs.get_context(
                    item["text"],
                    k=k,
                    every_represented_candidate=every_represented_candidate,
                )
                prompt         = self.__build_prompt(ctx["context"], item["text"])
                generated      = self.__generator(prompt,
                                                  output_type=self.__output_type,
                                                  max_new_tokens=50)
                answer         = self.__parse_predictions(ctx["context"], json.loads(generated))
                y_pred, y_true = self.__filter_items(list(zip(*answer))[1], item["ground_truth"])
                contexts       = self.__split_context_documents(ctx["context"])

                results.append(PredictionResult(
                    question            = prompt,
                    contexts            = contexts,
                    retrieved_resources = self.__get_retrieved_resources(contexts),
                    answer              = answer,
                    y_pred              = y_pred,
                    y_true              = y_true,
                ))
            except Exception as e:
                print(f"[SKIP] item '{item['text'][:50]}' → {e}")
                results.append(PredictionResult(question=item["text"]))

        return results
