import base64
import json
from typing import Any, Dict, List

import knowledge_base.output_converters
import pytest
from aws_lambda_powertools import Logger
from knowledge_base.output_converters import (
    parse_metadata,
    process_image_result,
    process_text_result,
    to_converse_api_content,
)
from utils.utils import safe_decode_base64


class TestOutputConverters:

    def test_empty_input(self):
        """
        Test that empty input returns only the opening and closing tags.
        """
        result = to_converse_api_content([])
        assert result == [{"text": "<context>"}, {"text": "</context>"}]

    def test_parse_metadata_2(self):
        """
        Test parse_metadata function with a valid JSON string input.
        """
        # Arrange
        test_metadata = '{"key": "value", "number": 42}'

        # Act
        result = parse_metadata(test_metadata)

        # Assert
        expected = {"key": "value", "number": 42}
        assert result == expected, f"Expected {expected}, but got {result}"

    def test_parse_metadata_dict_input(self):
        """
        Test parse_metadata function with a dictionary input.
        """
        # Arrange
        test_metadata = {"key": "value", "number": 42}

        # Act
        result = parse_metadata(test_metadata)

        # Assert
        assert result == test_metadata, f"Expected {test_metadata}, but got {result}"

    def test_parse_metadata_empty_input(self):
        """
        Test parse_metadata with empty input
        """
        result = parse_metadata("")
        assert result == {}, "Empty input should return an empty dictionary"

    def test_parse_metadata_invalid_json(self):
        """
        Test parse_metadata function with an invalid JSON string input.
        """
        # Arrange
        invalid_metadata = '{"key": "value", "number": 42'  # Missing closing brace

        # Act
        result = parse_metadata(invalid_metadata)

        # Assert
        assert result == {}, f"Expected empty dictionary, but got {result}"

    def test_parse_metadata_invalid_json_2(self):
        """
        Test parse_metadata with invalid JSON input
        """
        invalid_json = "{invalid json}"
        result = parse_metadata(invalid_json)
        assert result == {}, "Invalid JSON should return an empty dictionary"

    def test_parse_metadata_large_input(self):
        """
        Test parse_metadata with a very large input
        """
        large_input = '{"key": "' + "a" * 1000000 + '"}'
        result = parse_metadata(large_input)
        assert isinstance(result, dict), "Large input should still return a dictionary"
        assert len(result) == 1, "Large input should be parsed correctly"

    def test_parse_metadata_malformed_json(self):
        """
        Test parse_metadata with malformed JSON input
        """
        malformed_json = '{"key": "value",}'
        result = parse_metadata(malformed_json)
        assert result == {}, "Malformed JSON should return an empty dictionary"

    def test_parse_metadata_nested_dict(self):
        """
        Test parse_metadata with a nested dictionary input
        """
        nested_dict = {"key1": {"key2": "value"}}
        result = parse_metadata(nested_dict)
        assert result == nested_dict, "Nested dictionary should be returned as-is"

    def test_parse_metadata_with_dict_input(self):
        """
        Test parse_metadata function with a dictionary input.
        """
        # Arrange
        input_metadata = {"key": "value", "nested": {"inner": "data"}}

        # Act
        result = parse_metadata(input_metadata)

        # Assert
        assert result == input_metadata
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["nested"]["inner"] == "data"

    def test_process_image_result_2(self):
        """
        Test process_image_result when metadata is not present in the result.
        """
        # Prepare test data
        test_image = b"test_image_bytes"
        base64_image = base64.b64encode(test_image).decode("utf-8")
        result: Dict[str, Any] = {"image": base64_image, "format": "jpg"}

        # Call the function
        contents: List[Dict[str, Any]] = process_image_result(result)

        # Assert the results
        assert len(contents) == 1
        assert "image" in contents[0]
        assert contents[0]["image"]["format"] == "jpg"
        assert contents[0]["image"]["source"]["bytes"] == test_image
        assert "text" not in contents[0]

    def test_process_image_result_empty_image_string(self):
        """
        Test process_image_result with an empty image string.
        """
        result = {"image": ""}
        processed = process_image_result(result)
        assert processed[0]["image"]["source"]["bytes"] == b""

    def test_process_image_result_empty_input(self):
        """
        Test process_image_result with an empty input dictionary.
        """
        with pytest.raises(KeyError):
            process_image_result({})

    def test_process_image_result_invalid_metadata(self):
        """
        Test process_image_result with invalid metadata.
        """
        result = {"image": "base64_encoded_image", "metadata": "invalid_json"}
        processed = process_image_result(result)
        assert len(processed) == 1

    def test_process_image_result_missing_image_key(self):
        """
        Test process_image_result with a dictionary missing the 'image' key.
        """
        result = {"format": "jpg", "metadata": "{}"}
        with pytest.raises(KeyError):
            process_image_result(result)

    def test_process_image_result_non_dict_input(self):
        """
        Test process_image_result with non-dictionary input.
        """
        with pytest.raises(AttributeError):
            process_image_result("not a dictionary")

    def test_process_image_result_very_large_metadata(self):
        """
        Test process_image_result with very large metadata.
        """
        large_metadata = {"key": "x" * 1000000}  # 1MB of metadata
        result = {
            "image": "base64_encoded_image",
            "metadata": json.dumps(large_metadata),
        }
        processed = process_image_result(result)
        assert len(processed) == 2
        assert "<image_metadata>" in processed[1]["text"]
        assert len(processed[1]["text"]) > 1000000

    def test_process_text_result_empty_input(self):
        """
        Test process_text_result with empty input.
        """
        with pytest.raises(KeyError):
            process_text_result({})

    def test_process_text_result_incorrect_type(self):
        """
        Test process_text_result with incorrect input type.
        """
        with pytest.raises(AttributeError):
            process_text_result("not a dictionary")

    def test_process_text_result_invalid_input(self):
        """
        Test process_text_result with invalid input (missing 'text' key).
        """
        with pytest.raises(KeyError):
            process_text_result({"metadata": "{}"})

    def test_process_text_result_invalid_metadata_format(self):
        """
        Test process_text_result with invalid metadata format.
        """
        result = process_text_result(
            {"text": "Sample text", "metadata": "invalid json"}
        )
        assert result == {"text": "Sample text"}

    def test_process_text_result_with_empty_metadata(self):
        """
        Test process_text_result with text and empty metadata
        """
        result = {"text": "Sample text", "metadata": "{}"}
        expected_output = {"text": "Sample text"}
        assert process_text_result(result) == expected_output

    def test_process_text_result_without_metadata(self):
        """
        Test process_text_result with text and no metadata
        """
        result = {"text": "Sample text without metadata"}
        expected_output = {"text": "Sample text without metadata"}
        assert process_text_result(result) == expected_output

    def test_to_converse_api_content_3(self):
        """
        Test to_converse_api_content with unexpected result format
        """
        # Arrange
        query_results = [{"unexpected_key": "Some unexpected content"}]
        expected_output = [{"text": "<context>"}, {"text": "</context>"}]

        # Act
        result = to_converse_api_content(query_results)

        # Assert
        assert (
            result == expected_output
        ), f"Expected {expected_output}, but got {result}"
        # We can't directly assert that the warning was logged, but we can check that no exception was raised
        # and that the function returned the expected output despite the unexpected input

    def test_to_converse_api_content_with_examples(self):
        """
        Test to_converse_api_content with examples content type.
        """
        # Arrange
        query_results = [{"text": "Example 1"}, {"text": "Example 2"}]
        expected_output = [
            {"text": "<examples>"},
            {"text": "Example 1"},
            {"text": "Example 2"},
            {"text": "</examples>"},
        ]

        # Act
        result = to_converse_api_content(query_results, content_type="examples")

        # Assert
        assert result == expected_output

    def test_to_converse_api_content_with_unexpected_format(self):
        """
        Test to_converse_api_content with unexpected result format.
        """
        # Arrange
        query_results = [{"unexpected_key": "unexpected_value"}]
        expected_output = [{"text": "<context>"}, {"text": "</context>"}]

        # Act
        result = to_converse_api_content(query_results)

        # Assert
        assert result == expected_output
