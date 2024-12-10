import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import faiss
import numpy as np
import pytest
from knowledge_base.vector_db import FaissVectorStore


class TestVectorDb:

    @pytest.fixture
    def mock_embedding_function(self):
        def func(query: Dict[str, Any]) -> List[float]:
            return [0.1, 0.2, 0.3]  # Mock embedding

        return func

    @pytest.fixture
    def mock_faiss_index(self):
        index = faiss.IndexFlatL2(3)  # 3-dimensional vector
        index.add(np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], dtype=np.float32))
        return index

    def test_init_with_invalid_index_to_docstore_id(self):
        """
        Test initialization with an invalid index_to_docstore_id.
        """

        def dummy_embedding_function(data: Dict[str, Any]) -> List[float]:
            return [0.0]

        with pytest.raises(AttributeError):
            FaissVectorStore(
                embedding_function=dummy_embedding_function,
                index=None,
                index_to_docstore_id="not_a_dict",
            )

    def test_init_with_valid_parameters(self):
        """
        Test initialization of FaissVectorStore with valid parameters.
        """

        # Mock embedding function
        def mock_embedding_function(input_dict: Dict[str, Any]) -> List[float]:
            return [0.1, 0.2, 0.3]

        # Create a simple FAISS index
        dimension = 3
        index = faiss.IndexFlatL2(dimension)

        # Sample docstore and index_to_docstore_id
        docstore = {"doc1": {"text": "Sample text", "metadata": {"key": "value"}}}
        index_to_docstore_id = {0: "doc1"}

        # Initialize FaissVectorStore
        vector_store = FaissVectorStore(
            embedding_function=mock_embedding_function,
            index=index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id,
        )

        # Assert that the attributes are correctly set
        assert vector_store.embedding_function == mock_embedding_function
        assert vector_store.index == index
        assert vector_store.docstore == docstore
        assert vector_store.index_to_docstore_id == {0: "doc1"}

        # Test that the index_to_docstore_id keys are converted to integers
        vector_store = FaissVectorStore(
            embedding_function=mock_embedding_function,
            index=index,
            index_to_docstore_id={"0": "doc1"},
        )
        assert vector_store.index_to_docstore_id == {0: "doc1"}

    def test_load_successful(self):
        """
        Test successful loading of FaissVectorStore from files.
        """

        # Mock the embedding function
        def mock_embedding_function(
            query: Any, text: Optional[str] = None
        ) -> List[float]:
            return [0.1, 0.2, 0.3]

        # Get the absolute path for temp directory
        base_path = Path(__file__).parent.absolute()
        temp_base = base_path / "tmp"
        test_dir = temp_base / "test_faiss_vector_store"
        non_existent_dir = temp_base / "non_existent_dir"

        # Test non-existent directory
        with pytest.raises(FileNotFoundError):
            FaissVectorStore.load(str(non_existent_dir), mock_embedding_function)

        # Create a temporary directory
        test_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock FAISS index
        dimension = 3
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array([[0.1, 0.2, 0.3]], dtype=np.float32))
        faiss.write_index(index, str(test_dir / "index.faiss"))

        # Create a mock document store file
        doc_store_data = {
            "docstore": {"doc1": {"text": "Test document", "metadata": {}}},
            "index_to_docstore_id": {"0": "doc1"},
        }
        with open(test_dir / "documents.json", "w") as f:
            json.dump(doc_store_data, f)

        # Test loading
        with patch("faiss.read_index") as mock_read_index:
            mock_read_index.return_value = index
            vector_store = FaissVectorStore.load(str(test_dir), mock_embedding_function)

        assert isinstance(vector_store, FaissVectorStore)
        assert vector_store.embedding_function == mock_embedding_function
        assert isinstance(vector_store.index, faiss.Index)
        assert vector_store.docstore == doc_store_data["docstore"]
        assert vector_store.index_to_docstore_id == {0: "doc1"}

        # Clean up
        (test_dir / "index.faiss").unlink()
        (test_dir / "documents.json").unlink()
        test_dir.rmdir()

    def test_load_with_empty_directory_path(self):
        """
        Test load method with an empty directory path.
        """
        with pytest.raises(FileNotFoundError):
            FaissVectorStore.load(
                directory_path="",
                embedding_function=lambda x: [0.0],
            )

    def test_load_with_invalid_directory_path(self):
        """
        Test load method with an invalid directory path.
        """
        with pytest.raises(FileNotFoundError):
            FaissVectorStore.load(
                directory_path="/invalid/path",
                embedding_function=lambda x: [0.0],
            )

    def test_load_with_missing_index_file(self):
        """
        Test load method when the index file is missing.
        """
        with patch("os.path.join", return_value="non_existent_index.faiss"), patch(
            "faiss.read_index", side_effect=Exception("File not found")
        ):
            with pytest.raises(FileNotFoundError, match="Index file not found:"):
                FaissVectorStore.load(
                    directory_path="/tmp",
                    embedding_function=lambda x: [0.0],
                )

    def test_similarity_search_2(self):
        """
        Test similarity_search with a valid query dictionary, checking text-based results.
        """

        # Mock embedding function
        def mock_embedding_function(query: Dict[str, Any]) -> List[float]:
            return [0.1, 0.2, 0.3]

        # Create a mock FAISS index
        dimension = 3
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], dtype=np.float32))

        # Create mock docstore and index_to_docstore_id
        docstore = {
            "doc1": {"text": "Sample text 1", "metadata": {"key1": "value1"}},
            "doc2": {"text": "Sample text 2", "metadata": {"key2": "value2"}},
        }
        index_to_docstore_id = {0: "doc1", 1: "doc2"}

        # Initialize FaissVectorStore
        vector_store = FaissVectorStore(
            embedding_function=mock_embedding_function,
            index=index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id,
        )

        # Perform similarity search
        query = {"text": "sample query"}
        results = vector_store.similarity_search(query, k=2)

        # Assert the results
        assert len(results) == 2
        assert "distance" in results[0]
        assert "faiss_id" in results[0]
        assert "docstore_id" in results[0]
        assert "metadata" in results[0]
        assert "text" in results[0]
        assert results[0]["docstore_id"] in ["doc1", "doc2"]
        assert results[0]["text"] in ["Sample text 1", "Sample text 2"]

        # Test with invalid query type
        with pytest.raises(TypeError):
            vector_store.similarity_search("invalid query")

    def test_similarity_search_image_query(self):
        """
        Test similarity search with an image query when the document contains only an image.
        """

        # Mock embedding function
        def mock_embedding_function(query: Dict[str, Any]) -> List[float]:
            return [0.1, 0.2, 0.3]

        # Create a mock FAISS index
        dimension = 3
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array([[0.1, 0.2, 0.3]], dtype=np.float32))

        # Create a mock document store
        docstore = {
            "doc1": {
                "image": "base64_encoded_image_data",
                "metadata": {"some_key": "some_value"},
            }
        }

        # Create a mock index to docstore id mapping
        index_to_docstore_id = {0: "doc1"}

        # Initialize FaissVectorStore
        vector_store = FaissVectorStore(
            embedding_function=mock_embedding_function,
            index=index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id,
        )

        # Perform similarity search
        query = {"image": "some_image_data"}
        results = vector_store.similarity_search(query, k=1)

        # Assert the results
        assert len(results) == 1
        assert "distance" in results[0]
        assert results[0]["faiss_id"] == 0
        assert results[0]["docstore_id"] == "doc1"
        assert results[0]["metadata"] == {"some_key": "some_value"}
        assert "image" in results[0]
        assert "text" not in results[0]
        assert results[0]["image"] == "base64_encoded_image_data"

    def test_similarity_search_incorrect_type(self, vector_store):
        """Test similarity_search with incorrect input type"""
        with pytest.raises(TypeError):
            vector_store.similarity_search("not a dictionary")

    def test_similarity_search_large_k(self, vector_store):
        """Test similarity_search with k larger than index size"""
        results = vector_store.similarity_search({"text": "query"}, k=1000)
        assert len(results) <= 2

    def test_similarity_search_no_text_or_image(self):
        """
        Test similarity_search when the document has neither 'text' nor 'image' key.
        """

        # Mock embedding function
        def mock_embedding_function(query: Dict[str, Any]) -> List[float]:
            return [0.1, 0.2, 0.3]

        # Create a mock FAISS index
        dimension = 3
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array([[0.1, 0.2, 0.3]], dtype=np.float32))

        # Create a mock docstore and index_to_docstore_id
        docstore = {
            "doc1": {
                "metadata": {"key": "value"},
            }
        }
        index_to_docstore_id = {0: "doc1"}

        # Initialize FaissVectorStore
        vector_store = FaissVectorStore(
            embedding_function=mock_embedding_function,
            index=index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id,
        )

        # Perform similarity search
        query = {"text": "sample query"}
        results = vector_store.similarity_search(query, k=1)

        # Assert the results
        assert len(results) == 1
        assert results[0]["distance"] == pytest.approx(0.0)
        assert results[0]["faiss_id"] == 0
        assert results[0]["docstore_id"] == "doc1"
        assert results[0]["metadata"] == {"key": "value"}
        assert "text" not in results[0]
        assert "image" not in results[0]

    def test_similarity_search_nonexistent_docstore(self, vector_store):
        """Test similarity_search with a nonexistent docstore entry"""
        vector_store.docstore = {}  # Clear the docstore
        results = vector_store.similarity_search({"text": "query"})
        assert len(results) == 0

    def test_similarity_search_nonexistent_index(self, vector_store):
        """Test similarity_search with a nonexistent index"""
        vector_store.index_to_docstore_id = {}  # Clear the index mapping
        results = vector_store.similarity_search({"text": "query"})
        assert len(results) == 0

    def test_similarity_search_when_docstore_id_not_in_docstore(self):
        """
        Test similarity_search when the docstore_id is not in the docstore.
        """

        # Mock embedding function
        def mock_embedding_function(query: Dict[str, Any]) -> List[float]:
            return [0.1, 0.2, 0.3]

        # Create a mock FAISS index
        dimension = 3
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array([[0.1, 0.2, 0.3]], dtype=np.float32))

        # Create FaissVectorStore instance
        vector_store = FaissVectorStore(
            embedding_function=mock_embedding_function,
            index=index,
            docstore={},
            index_to_docstore_id={0: "doc1"},
        )

        # Perform similarity search
        query = {"text": "test query"}
        results = vector_store.similarity_search(query, k=1)

        # Assert that the result is an empty list
        assert results == []

    def test_similarity_search_when_index_not_in_docstore(self):
        """
        Test similarity_search when the index is not in the index_to_docstore_id mapping.
        """

        # Mock embedding function
        def mock_embedding_function(query: Dict[str, Any]) -> List[float]:
            return [0.1, 0.2, 0.3]

        # Create a mock FAISS index
        dimension = 3
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array([[0.1, 0.2, 0.3]], dtype=np.float32))

        # Initialize FaissVectorStore with empty docstore and index_to_docstore_id
        vector_store = FaissVectorStore(
            embedding_function=mock_embedding_function,
            index=index,
            docstore={},
            index_to_docstore_id={},
        )

        # Perform similarity search
        query = {"text": "test query"}
        results = vector_store.similarity_search(query, k=1)

        # Assert that the results list is empty
        assert (
            len(results) == 0
        ), "Expected empty results when index is not in index_to_docstore_id"

    def test_similarity_search_with_text_query(self):
        """
        Test similarity search with a text query when the document contains text data.
        """

        # Mock embedding function
        def mock_embedding_function(query: Dict[str, Any]) -> List[float]:
            return [0.1, 0.2, 0.3]

        # Create a mock FAISS index
        dimension = 3
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array([[0.1, 0.2, 0.3]], dtype=np.float32))

        # Create a mock docstore and index_to_docstore_id
        docstore = {"doc1": {"text": "Sample text", "metadata": {"key": "value"}}}
        index_to_docstore_id = {0: "doc1"}

        # Initialize FaissVectorStore
        vector_store = FaissVectorStore(
            embedding_function=mock_embedding_function,
            index=index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id,
        )

        # Perform similarity search
        query = {"text": "Sample query"}
        results = vector_store.similarity_search(query, k=1)

        # Assert the results
        assert len(results) == 1
        assert "distance" in results[0]
        assert results[0]["faiss_id"] == 0
        assert results[0]["docstore_id"] == "doc1"
        assert results[0]["metadata"] == {"key": "value"}
        assert results[0]["text"] == "Sample text"

    @pytest.fixture
    def vector_store(self, mock_embedding_function, mock_faiss_index):
        docstore = {
            "doc1": {"text": "Sample text 1", "metadata": {"key1": "value1"}},
            "doc2": {"text": "Sample text 2", "metadata": {"key2": "value2"}},
        }
        index_to_docstore_id = {0: "doc1", 1: "doc2"}
        return FaissVectorStore(
            mock_embedding_function, mock_faiss_index, docstore, index_to_docstore_id
        )
