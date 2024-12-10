from typing import Any, Dict, List, Union

import pytest
from utils.converse_stream.format_converter import (
    from_bedrock_converse_to_bedrock_invoke,
)


class TestFormatConverter:

    def test_empty_dictionary_input(self):
        """
        Test that an empty dictionary input raises a ValueError.
        """
        with pytest.raises(
            ValueError, match="Dictionary must contain either 'text' or 'image' key"
        ):
            from_bedrock_converse_to_bedrock_invoke({})

    def test_from_bedrock_converse_to_bedrock_invoke_2(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with a dictionary containing both text and image
        """
        # Arrange
        converse_content = {
            "text": "Hello, world!",
            "image": {"source": {"bytes": b"image_data"}},
        }

        # Act
        result = from_bedrock_converse_to_bedrock_invoke(converse_content)

        # Assert
        assert isinstance(result, dict)
        assert "inputText" in result
        assert "inputImage" in result
        assert result["inputText"] == "Hello, world!"
        assert result["inputImage"] == b"image_data"

    def test_from_bedrock_converse_to_bedrock_invoke_3(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with an invalid dictionary input.
        """
        # Arrange
        invalid_content = {"invalid_key": "some_value"}

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            from_bedrock_converse_to_bedrock_invoke(invalid_content)

        assert (
            str(exc_info.value)
            == "Dictionary must contain either 'text' or 'image' key"
        )

    def test_from_bedrock_converse_to_bedrock_invoke_image_only(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with a dictionary containing only an image.
        """
        # Arrange
        image_data = b"mock_image_bytes"
        converse_content = {"image": {"source": {"bytes": image_data}}}

        # Act
        result = from_bedrock_converse_to_bedrock_invoke(converse_content)

        # Assert
        assert isinstance(result, dict)
        assert "inputImage" in result
        assert result["inputImage"] == image_data
        assert "inputText" not in result

    def test_from_bedrock_converse_to_bedrock_invoke_invalid_dict(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with an invalid dictionary input.
        """
        converse_content = {"invalid_key": "some value"}

        with pytest.raises(ValueError) as excinfo:
            from_bedrock_converse_to_bedrock_invoke(converse_content)

        assert (
            str(excinfo.value) == "Dictionary must contain either 'text' or 'image' key"
        )

    def test_from_bedrock_converse_to_bedrock_invoke_invalid_type(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with an invalid input type.
        """
        converse_content = "invalid input"

        with pytest.raises(TypeError) as excinfo:
            from_bedrock_converse_to_bedrock_invoke(converse_content)

        assert (
            str(excinfo.value)
            == "Input must be either a dictionary or a list of dictionaries"
        )

    def test_from_bedrock_converse_to_bedrock_invoke_list_with_text_and_image(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with a list containing both text and image inputs.
        """
        converse_content = [
            {"text": "Describe this image"},
            {"image": {"source": {"bytes": b"image_data"}}},
        ]
        expected_output = {
            "inputText": "Describe this image",
            "inputImage": b"image_data",
        }

        result = from_bedrock_converse_to_bedrock_invoke(converse_content)

        assert result == expected_output

    def test_from_bedrock_converse_to_bedrock_invoke_text_only(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with a dictionary containing only text input.
        """
        converse_content = {"text": "Hello, world!"}
        expected_output = {"inputText": "Hello, world!"}

        result = from_bedrock_converse_to_bedrock_invoke(converse_content)

        assert result == expected_output
        assert "inputImage" not in result

    def test_from_bedrock_converse_to_bedrock_invoke_with_image_only(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with a dictionary containing only image.
        """
        converse_content = {"image": {"source": {"bytes": b"image_data"}}}

        expected_result = {"inputImage": b"image_data"}

        result = from_bedrock_converse_to_bedrock_invoke(converse_content)
        assert result == expected_result

    def test_from_bedrock_converse_to_bedrock_invoke_with_invalid_dict(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with an invalid dictionary (no text or image).
        """
        converse_content = {"invalid_key": "invalid_value"}

        with pytest.raises(
            ValueError, match="Dictionary must contain either 'text' or 'image' key"
        ):
            from_bedrock_converse_to_bedrock_invoke(converse_content)

    def test_from_bedrock_converse_to_bedrock_invoke_with_invalid_list(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with an invalid list (more than 2 items).
        """
        converse_content = [
            {"text": "Hello"},
            {"image": {"source": {"bytes": b"image_data"}}},
            {"text": "Extra item"},
        ]

        with pytest.raises(
            ValueError,
            match="List must contain one or two dictionaries including \(text and image\)",
        ):
            from_bedrock_converse_to_bedrock_invoke(converse_content)

    def test_from_bedrock_converse_to_bedrock_invoke_with_invalid_type(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with an invalid input type.
        """
        converse_content = "Invalid input"

        with pytest.raises(
            TypeError,
            match="Input must be either a dictionary or a list of dictionaries",
        ):
            from_bedrock_converse_to_bedrock_invoke(converse_content)

    def test_from_bedrock_converse_to_bedrock_invoke_with_list(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with a list of dictionaries.
        """
        converse_content = [
            {"text": "Hello, world!"},
            {"image": {"source": {"bytes": b"image_data"}}},
        ]

        expected_result = {"inputText": "Hello, world!", "inputImage": b"image_data"}

        result = from_bedrock_converse_to_bedrock_invoke(converse_content)
        assert result == expected_result

    def test_from_bedrock_converse_to_bedrock_invoke_with_text_and_image(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with a dictionary containing both text and image.
        """
        converse_content = {
            "text": "Hello, world!",
            "image": {"source": {"bytes": b"image_data"}},
        }

        expected_result = {"inputText": "Hello, world!", "inputImage": b"image_data"}

        result = from_bedrock_converse_to_bedrock_invoke(converse_content)
        assert result == expected_result

    def test_from_bedrock_converse_to_bedrock_invoke_with_text_only(self):
        """
        Test from_bedrock_converse_to_bedrock_invoke with a dictionary containing only text.
        """
        converse_content = {"text": "Hello, world!"}

        expected_result = {"inputText": "Hello, world!"}

        result = from_bedrock_converse_to_bedrock_invoke(converse_content)
        assert result == expected_result

    def test_image_dictionary_missing_nested_keys(self):
        """
        Test that an image dictionary missing nested keys raises a KeyError.
        """
        with pytest.raises(KeyError):
            from_bedrock_converse_to_bedrock_invoke({"image": {}})

    def test_incorrect_input_type(self):
        """
        Test that an input of incorrect type (neither dict nor list) raises a TypeError.
        """
        with pytest.raises(
            TypeError,
            match="Input must be either a dictionary or a list of dictionaries",
        ):
            from_bedrock_converse_to_bedrock_invoke("not_a_dict_or_list")

    def test_invalid_dictionary_keys(self):
        """
        Test that a dictionary with invalid keys raises a ValueError.
        """
        with pytest.raises(
            ValueError, match="Dictionary must contain either 'text' or 'image' key"
        ):
            from_bedrock_converse_to_bedrock_invoke({"invalid_key": "value"})

    def test_invalid_input_type_raises_type_error(self):
        """
        Test that from_bedrock_converse_to_bedrock_invoke raises a TypeError
        when the input is neither a dictionary nor a list.
        """
        # Arrange
        invalid_input = "This is a string, not a dict or list"

        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            from_bedrock_converse_to_bedrock_invoke(invalid_input)

        assert (
            str(exc_info.value)
            == "Input must be either a dictionary or a list of dictionaries"
        )

    def test_invalid_list_input_raises_value_error(self):
        """
        Test that providing a list with more than two dictionaries raises a ValueError.
        """
        invalid_input = [
            {"text": "some text"},
            {"image": {"source": {"bytes": b"image_data"}}},
            {"text": "extra text"},
        ]

        with pytest.raises(ValueError) as exc_info:
            from_bedrock_converse_to_bedrock_invoke(invalid_input)

        assert (
            str(exc_info.value)
            == "List must contain one or two dictionaries including (text and image)"
        )

    def test_list_with_invalid_dictionary_keys(self):
        """
        Test that a list with dictionaries containing invalid keys raises a ValueError.
        """
        input_list = [{"invalid_key": "value"}, {"another_invalid_key": "value"}]
        with pytest.raises(
            ValueError,
            match="Each dictionary must contain either 'text' or 'image' key",
        ):
            from_bedrock_converse_to_bedrock_invoke(input_list)

    def test_list_with_mixed_valid_and_invalid_dictionaries(self):
        """
        Test that a list with one valid and one invalid dictionary raises a ValueError.
        """
        input_list = [{"text": "valid text"}, {"invalid_key": "value"}]
        with pytest.raises(
            ValueError,
            match="Each dictionary must contain either 'text' or 'image' key",
        ):
            from_bedrock_converse_to_bedrock_invoke(input_list)

    def test_list_with_more_than_two_dictionaries(self):
        """
        Test that a list with more than two dictionaries raises a ValueError.
        """
        input_list = [
            {"text": "text1"},
            {"image": {"source": {"bytes": b"image_data"}}},
            {"text": "text2"},
        ]
        with pytest.raises(
            ValueError,
            match="List must contain one or two dictionaries including \(text and image\)",
        ):
            from_bedrock_converse_to_bedrock_invoke(input_list)

    def test_list_with_non_dictionary_item(self):
        """
        Test that a list containing a non-dictionary item raises a TypeError.
        """
        input_list = [{"text": "text"}, "not_a_dict"]
        with pytest.raises(TypeError, match="Each item in list must be a dictionary"):
            from_bedrock_converse_to_bedrock_invoke(input_list)
