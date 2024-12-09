import base64
import re

import pytest
from utils.utils import is_base64, remove_base64_prefix, safe_decode_base64


class TestUtils:

    def test_is_base64_empty_string(self):
        """
        Test that is_base64 returns True for an empty string (which is valid Base64)
        """
        assert is_base64("") == True

    def test_is_base64_invalid_input(self):
        """Test is_base64 with invalid input"""
        assert not is_base64("This is not a base64 string")

    def test_is_base64_invalid_string(self):
        """
        Test that is_base64 returns False for an invalid Base64 string
        """
        invalid_base64 = "This is not a Base64 encoded string!"
        assert is_base64(invalid_base64) == False

    def test_is_base64_non_ascii(self):
        """
        Test that is_base64 handles non-ASCII characters correctly
        """
        non_ascii = base64.b64encode("こんにちは".encode("utf-8")).decode()
        assert is_base64(non_ascii) == True

    def test_is_base64_non_base64_characters(self):
        """Test is_base64 with non-base64 characters"""
        assert not is_base64("SGVsbG8gV29ybGQ!@#")

    def test_is_base64_non_string_input(self):
        """Test is_base64 with non-string input"""
        assert not is_base64(123)
        assert not is_base64(None)
        assert not is_base64([])

    def test_is_base64_unicode_input(self):
        """Test is_base64 with Unicode input"""
        assert not is_base64("こんにちは世界")

    def test_is_base64_valid_string(self):
        """
        Test that is_base64 returns True for a valid Base64 encoded string
        """
        valid_base64 = base64.b64encode(b"Hello, World!").decode()
        assert is_base64(valid_base64) == True

    def test_remove_base64_prefix_edge_case_partial_prefix(self):
        """
        Test remove_base64_prefix with a partial prefix.
        """
        partial_prefix = "data:image/png;base"
        result = remove_base64_prefix(partial_prefix)
        assert result == partial_prefix, "Partial prefix should return unchanged"

    def test_remove_base64_prefix_empty_input(self):
        """
        Test remove_base64_prefix with an empty string input.
        """
        result = remove_base64_prefix("")
        assert result == "", "Empty string should return empty string"

    def test_remove_base64_prefix_invalid_input(self):
        """
        Test remove_base64_prefix with invalid input (no prefix).
        """
        invalid_input = "not a base64 string"
        result = remove_base64_prefix(invalid_input)
        assert result == invalid_input, "Invalid input should return unchanged"

    def test_remove_base64_prefix_with_empty_string(self):
        """
        Test remove_base64_prefix with an empty string.
        """
        input_string = ""
        expected_output = ""

        result = remove_base64_prefix(input_string)

        assert result == expected_output, f"Expected empty string, but got {result}"

    def test_remove_base64_prefix_with_valid_prefix(self):
        """
        Test remove_base64_prefix with a string containing a valid Base64 prefix.
        """
        input_string = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
        expected_output = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="

        result = remove_base64_prefix(input_string)

        assert (
            result == expected_output
        ), f"Expected {expected_output}, but got {result}"

    def test_remove_base64_prefix_without_prefix(self):
        """
        Test remove_base64_prefix with a string that doesn't contain a Base64 prefix.
        """
        input_string = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
        expected_output = input_string

        result = remove_base64_prefix(input_string)

        assert (
            result == expected_output
        ), f"Expected {expected_output}, but got {result}"

    def test_safe_decode_base64_empty_input(self):
        """
        Test safe_decode_base64 with empty input
        """
        result = safe_decode_base64("")
        assert result == b"", "Empty input should return empty bytes"

    def test_safe_decode_base64_empty_string(self):
        """
        Test safe_decode_base64 with an empty string.
        """
        # Arrange
        empty_string = ""

        # Act
        result = safe_decode_base64(empty_string)

        # Assert
        assert result == empty_string.encode()

    def test_safe_decode_base64_incorrect_format(self):
        """
        Test safe_decode_base64 with incorrect Base64 format
        """
        result = safe_decode_base64("aGVsbG8=world")  # 'hello' in Base64 + 'world'
        assert (
            result == b"aGVsbG8=world"
        ), "Incorrectly formatted Base64 should return encoded original string"

    def test_safe_decode_base64_invalid_input(self):
        """
        Test safe_decode_base64 with an invalid Base64 string.
        """
        # Arrange
        invalid_string = "This is not a Base64 encoded string!"

        # Act
        result = safe_decode_base64(invalid_string)

        # Assert
        assert result == invalid_string.encode()

    def test_safe_decode_base64_invalid_input_2(self):
        """
        Test safe_decode_base64 with invalid Base64 input
        """
        result = safe_decode_base64("invalid_base64!")
        assert (
            result == b"invalid_base64!"
        ), "Invalid Base64 input should return encoded original string"

    def test_safe_decode_base64_non_ascii(self):
        """
        Test safe_decode_base64 with non-ASCII input
        """
        non_ascii = "こんにちは"  # Japanese for "hello"
        result = safe_decode_base64(non_ascii)
        assert result == non_ascii.encode(
            "utf-8"
        ), "Non-ASCII input should be UTF-8 encoded"

    def test_safe_decode_base64_valid_input(self):
        """
        Test safe_decode_base64 with a valid Base64 encoded string.
        """
        # Arrange
        test_string = "Hello, World!"
        encoded_string = base64.b64encode(test_string.encode()).decode()

        # Act
        result = safe_decode_base64(encoded_string)

        # Assert
        assert result == test_string.encode()

    def test_safe_decode_base64_with_prefix(self):
        """
        Test safe_decode_base64 with a valid Base64 encoded string with a prefix.
        """
        # Arrange
        test_string = "Hello, World!"
        encoded_string = base64.b64encode(test_string.encode()).decode()
        prefixed_string = f"data:image/png;base64,{encoded_string}"

        # Act
        result = safe_decode_base64(prefixed_string)

        # Assert
        assert result == test_string.encode()

    def test_safe_decode_base64_with_prefix_2(self):
        """
        Test safe_decode_base64 with Base64 prefix
        """
        prefix = "data:image/png;base64,"
        encoded = base64.b64encode(b"image data").decode()
        input_string = prefix + encoded
        result = safe_decode_base64(input_string)
        assert result == b"image data", "Base64 with prefix should be correctly decoded"
