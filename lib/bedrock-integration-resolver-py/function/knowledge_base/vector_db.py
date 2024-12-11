import json
import os
from typing import Any, Callable, Dict, Iterable, List, Optional

import faiss
import numpy as np


class FaissVectorStore:
    """
    A vector store that uses FAISS for similarity search and document storage.

    Attributes:
        embedding_function (Callable[[Dict[str, Any]], List[float]]): A function that takes a dictionary with 'image' and optional 'text' keys and returns its embedding.
        index (Any): A FAISS index object used for similarity search.
        docstore (Dict[str, Dict[str, Any]]): A dictionary that stores the document data, where the keys are document IDs.
        index_to_docstore_id (Dict[int, str]): A dictionary that maps FAISS index IDs to document IDs.
    """

    def __init__(
        self,
        embedding_function: Callable[[Dict[str, Any]], List[float]],
        index: Any,
        docstore: Dict[str, Dict[str, Any]] = {},
        index_to_docstore_id: Dict[int, str] = {},
    ):
        """
        Initialize a FaissVectorStore instance.

        Args:
            embedding_function (Callable[[Dict[str, Any]], List[float]]): A function that takes a dictionary with 'image' and optional 'text' keys and returns its embedding.
            index (Any): A FAISS index object used for similarity search.
            docstore (Dict[str, Dict[str, Any]], optional): A dictionary to store document data. Defaults to {}.
            index_to_docstore_id (Dict[int, str], optional): A dictionary mapping FAISS index IDs to document IDs. Defaults to {}.
        """
        self.embedding_function = embedding_function
        self.index = index
        self.docstore = docstore
        self.index_to_docstore_id = {int(k): v for k, v in index_to_docstore_id.items()}

    def similarity_search(
        self, query: Dict[str, Any], k: int = 1, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Perform a similarity search on the vector index using the given query.

        Args:
            query (Dict[str, Any]): Either a dictionary with only "text" key or with 'image' key and optional 'text' key for image queries.
            k (int, optional): The number of nearest neighbors to return. Defaults to 1.
            **kwargs: Additional keyword arguments to pass to the search function.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the search results.
        """
        if isinstance(query, dict):
            query_embedding = self.embedding_function(query)
        else:
            raise TypeError("Query must be a dictionary")

        _vector = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(_vector, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx in self.index_to_docstore_id:
                docstore_id = self.index_to_docstore_id[idx]
                if docstore_id in self.docstore:
                    doc_data = self.docstore[docstore_id]
                    result = {
                        "distance": distances[0][i],
                        "faiss_id": idx,
                        "docstore_id": docstore_id,
                        "metadata": doc_data.get("metadata", {}),
                    }
                    if "text" in doc_data:
                        result["text"] = doc_data["text"]
                    elif "image" in doc_data:
                        result["image"] = doc_data["image"]
                    results.append(result)

        return results

    @classmethod
    def load(
        cls,
        directory_path: str,
        embedding_function: Callable[[Any, Optional[str]], List[float]],
        index_file_name: Optional[str] = "index.faiss",
        document_store_file_name: Optional[str] = "documents.json",
    ) -> "FaissVectorStore":
        """
        Load a FaissVectorStore from files.

        Args:
            directory_path (str): The path to the directory containing the index and document store files.
            embedding_function: Callable[[Any, Optional[str]], List[float]]: The embedding function used
            index_file_name (str, optional): The name of the index file. Defaults to "index.faiss".
            document_store_file_name (str, optional): The name of the document store file. Defaults to "documents.json".

        Returns:
            FaissVectorStore: A new instance of FaissVectorStore loaded from the files.

        Raises:
            FileNotFoundError: If the specified index or document store file does not exist.
            json.JSONDecodeError: If the document store file contents are not valid JSON.
            Exception: If there is an error while reading the FAISS index file.
        """
        index_path = os.path.join(directory_path, index_file_name)
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")

        try:
            faiss_index = faiss.read_index(index_path)
        except Exception as e:
            raise Exception(f"Error reading FAISS index file: {index_path}") from e

        document_store_file_path = os.path.join(
            directory_path, document_store_file_name
        )
        if not os.path.exists(document_store_file_path):
            raise FileNotFoundError(
                f"Document store file not found: {document_store_file_path}"
            )
        try:
            with open(document_store_file_path, "r") as file:
                loaded_data = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {document_store_file_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON file: {document_store_file_path}", e.doc, e.pos
            )

        return cls(
            embedding_function=embedding_function,
            index=faiss_index,
            docstore=loaded_data["docstore"],
            index_to_docstore_id=loaded_data["index_to_docstore_id"],
        )
