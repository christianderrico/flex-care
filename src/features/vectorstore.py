"""
FAISS-based vector store for FHIR resource retrieval.
"""

import json
import os
import string
from pathlib import Path

from huggingface_hub import login
from langchain_community.vectorstores import FAISS
from langchain_core.documents.base import Document
from langchain_huggingface import HuggingFaceEmbeddings


class VectorStore:
    """
    Builds and queries a FAISS vectorstore from serialised resource documents.

    Parameters
    ----------
    embeddings : str
        HuggingFace model name for the embedding model.
    docs : list[str]
        JSON-serialised resource points as returned by ``Loader.docs``.
    device : str, optional
        Device for the embedding model, by default ``"auto"``.
    normalize : bool, optional
        Whether to normalize embeddings, by default ``False``.
    """

    __LOGGED_IN = False

    def __init__(
        self,
        embeddings: str,
        docs:       list[str],
        device:     str  = "cuda",
        normalize:  bool = False,
    ):
        self.__docs       = docs
        self.__embeddings = self.__load_embeddings(embeddings, device, normalize)
        self.__db: FAISS | None = None

    @classmethod
    def __ensure_hf_login(cls) -> None:
        """Login to HuggingFace Hub once per process."""
        if not cls.__LOGGED_IN:
            token = os.environ.get("HF_KEY")
            if not token:
                raise EnvironmentError(
                    "HuggingFace token not found. "
                    "Set the HF_KEY environment variable."
                )
            login(token=token)
            cls.__LOGGED_IN = True

    def __load_embeddings(
        self,
        model:     str,
        device:    str,
        normalize: bool,
    ) -> HuggingFaceEmbeddings:
        self.__ensure_hf_login()
        return HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": normalize},
        )

    @staticmethod
    def __iter_chunks(items: list[str], size: int):
        for i in range(0, len(items), size):
            yield items[i:i + size]

    @staticmethod
    def __doc_to_chunks(doc: str, chunk_size: int) -> list[str]:
        parsed   = json.loads(doc)
        resource = parsed["resource"]

        def make_chunk(content: str) -> str:
            return json.dumps({"resource": resource, "content": content})

        chunked_keys = ("examples", "documentation")
        return [
            make_chunk("\n".join(group))
            for key, value in parsed.items()
            if key != "resource"
            for group in (
                VectorStore.__iter_chunks(value, chunk_size)
                if key in chunked_keys
                else [[value]]
            )
        ]

    def __build_chunks(self, chunk_size: int) -> list[str]:
        return [
            chunk
            for doc in self.__docs
            for chunk in VectorStore.__doc_to_chunks(doc, chunk_size)
        ]

    @property
    def db(self) -> FAISS:
        """
        Return the FAISS index.

        Raises
        ------
        RuntimeError
            If the index has not been built or loaded yet.
        """
        if self.__db is None:
            raise RuntimeError(
                "Vectorstore not ready. Call build() or load() first."
            )
        return self.__db

    def build(self, chunk_size: int = 6, save_path: Path | None = None) -> None:
        """
        Build the FAISS index from the documents passed at construction time.

        Parameters
        ----------
        chunk_size : int, optional
            Number of items per chunk for ``examples`` and ``documentation``
            fields, by default ``6``.
        save_path : Path, optional
            If provided, the index is persisted to disk at this path.
        """
        docs     = [Document(chunk) for chunk in self.__build_chunks(chunk_size)]
        self.__db = FAISS.from_documents(docs, self.__embeddings)
        if save_path:
            self.__db.save_local(str(save_path))
        return self

    def load(self, load_path: Path) -> None:
        """
        Load a previously saved FAISS index from disk.

        Parameters
        ----------
        load_path : Path
            Directory where the FAISS index was saved.

        Raises
        ------
        RuntimeError
            If no index is found at ``load_path``.
        """
        if not load_path.exists():
            raise RuntimeError(
                f"No index found at {load_path}. Call build() first."
            )
        self.__db = FAISS.load_local(
            str(load_path),
            self.__embeddings,
            allow_dangerous_deserialization=True,
        )

    @staticmethod
    def __gen_labels() -> list[str]:
        labels = [
            "".join(
                string.ascii_uppercase[(i // 26 ** k) % 26]
                for k in reversed(range((i.bit_length() + 4) // 5 + 1))
            )
            for i in range(65)
        ]
        return [l.lstrip("A") or "A" for l in labels]

    def get_context(
        self,
        query:                       str,
        k:                           int  = 10,
        every_represented_candidate: bool = False,
    ) -> dict:
        """
        Retrieve the top-k most relevant FHIR resource chunks for a query.

        Parameters
        ----------
        query : str
            Free-text clinical description to search against the vector store.
        k : int, optional
            Number of results to return, by default ``10``.
        every_represented_candidate : bool, optional
            If ``True``, returns at most one chunk per resource type — i.e.
            the top-k results cover k distinct FHIR resources.
            If ``False``, returns the top-k chunks regardless of resource type,
            so the same resource may appear multiple times.

        Returns
        -------
        dict
            - ``context``   (str)       : Labelled chunks formatted as
            ``"<LABEL>) <Resource>: <content>"`` and joined by newline,
            ready to be injected into the prompt template.
            - ``resources`` (list[str]) : Ordered list of matched resource
            names (lowercase), in the same order as ``context``.

        Raises
        ------
        RuntimeError
            If the vector store has not been built or loaded yet.
        """
        n_docs  = 1000 if every_represented_candidate else k
        results = self.db.similarity_search_with_score(query=query, k=n_docs)
        labels  = self.__gen_labels()

        output, resources = [], []
        for doc, _ in results:
            page = json.loads(doc.page_content)
            res  = page["resource"]
            if every_represented_candidate and res.lower() in resources:
                continue
            if len(resources) >= k:
                break
            resources.append(res.lower())
            output.append(f"{labels[len(output)]}) {res}: {page['content']}")

        return {"context": "\n".join(output), "resources": resources}
