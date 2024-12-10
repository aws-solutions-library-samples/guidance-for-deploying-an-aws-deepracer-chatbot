from decimal import ROUND_DOWN, Decimal
from unittest.mock import MagicMock, patch

import pytest
from boto3.dynamodb.types import Binary
from botocore.exceptions import ClientError
from utils.dynamo_helpers import (
    generate_update_query,
    get_item,
    replace_decimal_with_float,
    replace_floats_with_decimal,
)


class TestDynamoHelpers:

    def test_generate_update_query_with_float(self):
        fields = {"id": "123", "name": "test", "score": 95.5}
        key_fields = ["id"]

        result = generate_update_query(fields, key_fields)

        expected = {
            "UpdateExpression": "set #name = :name, #score = :score",
            "ExpressionAttributeNames": {"#name": "name", "#score": "score"},
            "ExpressionAttributeValues": {
                ":name": "test",
                ":score": Decimal("95.5000"),
            },
        }

        assert result == expected, f"Expected {expected}, but got {result}"

    def test_generate_update_query_with_float_values(self):
        """
        Test generate_update_query with float values to ensure they're converted to Decimal.
        """
        result = generate_update_query({"float_key": 3.14159})
        assert isinstance(result["ExpressionAttributeValues"][":float_key"], Decimal)
        assert result["ExpressionAttributeValues"][":float_key"] == Decimal("3.1415")

    def test_generate_update_query_with_incorrect_type(self):
        """
        Test generate_update_query with incorrect input types.
        """
        result = generate_update_query({"key": [1, 2, 3]})
        assert result["ExpressionAttributeValues"][":key"] == [1, 2, 3]

    def test_generate_update_query_with_invalid_input(self):
        """
        Test generate_update_query with invalid input (non-dict).
        """
        with pytest.raises(AttributeError):
            generate_update_query("invalid_input")

    def test_generate_update_query_with_non_key_fields(self):
        """
        Test generate_update_query with fields not in key_fields.
        Ensures the function generates the correct update expression and attribute mappings.
        """
        # Arrange
        fields = {"id": "123", "name": "John Doe", "age": 30, "score": 95.5}
        key_fields = ["id"]

        # Act
        result = generate_update_query(fields, key_fields)

        # Assert
        expected_update_expression = "set #name = :name, #age = :age, #score = :score"
        expected_attribute_names = {"#name": "name", "#age": "age", "#score": "score"}
        expected_attribute_values = {
            ":name": "John Doe",
            ":age": 30,
            ":score": Decimal("95.5000"),
        }

        assert result["UpdateExpression"] == expected_update_expression
        assert result["ExpressionAttributeNames"] == expected_attribute_names
        assert result["ExpressionAttributeValues"] == expected_attribute_values

    @patch("utils.dynamo_helpers.ddb_client")
    def test_get_item_client_error(self, mock_ddb_client):
        """
        Test handling of ClientError when fetching an item.
        """
        # Arrange
        table_name = "test_table"
        key = {"id": "789"}
        mock_ddb_client.get_item.side_effect = ClientError(
            error_response={"Error": {"Message": "Test error"}},
            operation_name="GetItem",
        )

        # Act & Assert
        with pytest.raises(ClientError):
            get_item(table_name, key)

    @patch("utils.dynamo_helpers.ddb_client")
    def test_get_item_client_error_2(self, mock_ddb_client):
        """
        Test get_item when DynamoDB client raises a ClientError.
        """
        mock_ddb_client.get_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Table not found",
                }
            },
            "GetItem",
        )

        with pytest.raises(ClientError):
            get_item("non_existent_table", {"id": "123"})

    @patch("utils.dynamo_helpers.ddb_client")
    def test_get_item_non_existent_item(self, mock_ddb_client):
        """
        Test get_item when the requested item does not exist.
        """
        mock_ddb_client.get_item.return_value = {}

        result = get_item("table_name", {"id": "non_existent"})
        assert result is None

    @patch("utils.dynamo_helpers.ddb_client")
    def test_get_item_not_found(self, mock_ddb_client):
        """
        Test when the item is not found in DynamoDB.
        """
        # Arrange
        table_name = "test_table"
        key = {"id": "456"}
        mock_ddb_client.get_item.return_value = {}

        # Act
        result = get_item(table_name, key)

        # Assert
        mock_ddb_client.get_item.assert_called_once_with(TableName=table_name, Key=key)
        assert result is None

    @patch("utils.dynamo_helpers.ddb_client")
    def test_get_item_success(self, mock_ddb_client):
        """
        Test successful retrieval of an item from DynamoDB.
        """
        # Arrange
        table_name = "test_table"
        key = {"id": "123"}
        mock_response = {
            "Item": {
                "id": "123",
                "name": "Test Item",
                "price": Decimal("10.99"),
                "quantity": Decimal("5"),
            }
        }
        mock_ddb_client.get_item.return_value = mock_response

        # Act
        result = get_item(table_name, key)

        # Assert
        mock_ddb_client.get_item.assert_called_once_with(TableName=table_name, Key=key)
        assert result == {
            "id": "123",
            "name": "Test Item",
            "price": 10.99,
            "quantity": 5,
        }

    @patch("utils.dynamo_helpers.ddb_client")
    def test_get_item_when_client_error_raised(self, mock_ddb_client):
        """
        Test get_item when a ClientError is raised.
        """
        # Arrange
        table_name = "test_table"
        key = {"id": "test_id"}
        mock_ddb_client.get_item.side_effect = ClientError(
            error_response={"Error": {"Message": "Test error"}},
            operation_name="GetItem",
        )

        # Act & Assert
        with pytest.raises(ClientError):
            get_item(table_name, key)

        mock_ddb_client.get_item.assert_called_once_with(TableName=table_name, Key=key)

    @patch("utils.dynamo_helpers.ddb_client")
    def test_get_item_when_item_not_found(self, mock_ddb_client):
        """
        Test get_item when the item is not found in the DynamoDB table.
        """
        # Arrange
        table_name = "test_table"
        key = {"id": "test_id"}
        mock_response = {
            "ResponseMetadata": {"RequestId": "123456"}
        }  # No 'Item' in response
        mock_ddb_client.get_item.return_value = mock_response

        # Act
        result = get_item(table_name, key)

        # Assert
        assert result is None
        mock_ddb_client.get_item.assert_called_once_with(TableName=table_name, Key=key)

    def test_non_decimal_input(self):
        """
        Test that replace_decimal_with_float returns the input unchanged if it's not a Decimal, list, or dict.
        """
        # Arrange
        input_string = "test"

        # Act
        result = replace_decimal_with_float(input_string)

        # Assert
        assert result == "test"

    def test_replace_binary_with_byte_string(self):
        """
        Test that replace_decimal_with_float correctly handles Binary objects.
        """
        # Arrange
        binary_input = Binary(b"test")

        # Act
        result = replace_decimal_with_float(binary_input)

        # Assert
        assert isinstance(result, bytes)
        assert result == b"test"

    def test_replace_decimal_in_dict(self):
        """
        Test that replace_decimal_with_float correctly handles Decimals within a dictionary.
        """
        # Arrange
        input_dict = {"a": Decimal("1.0"), "b": Decimal("2.5"), "c": 3}

        # Act
        result = replace_decimal_with_float(input_dict)

        # Assert
        assert isinstance(result, dict)
        assert result == {"a": 1, "b": 2.5, "c": 3}

    def test_replace_decimal_in_list(self):
        """
        Test that replace_decimal_with_float correctly handles Decimals within a list.
        """
        # Arrange
        input_list = [Decimal("1.0"), Decimal("2.5"), 3]

        # Act
        result = replace_decimal_with_float(input_list)

        # Assert
        assert isinstance(result, list)
        assert result == [1, 2.5, 3]

    def test_replace_decimal_with_float(self):
        """
        Test that replace_decimal_with_float converts a Decimal to a float when it's not a whole number.
        """
        # Arrange
        decimal_input = Decimal("5.5")

        # Act
        result = replace_decimal_with_float(decimal_input)

        # Assert
        assert isinstance(result, float)
        assert result == 5.5

    def test_replace_decimal_with_float_2(self):
        """
        Test the replace_decimal_with_float
        """
        # Arrange
        test_input = {
            "decimal": Decimal("10.5"),
            "integer": Decimal("5"),
            "list": [Decimal("1.1"), Decimal("2.2")],
            "nested": {"a": Decimal("3.3"), "b": [Decimal("4.4")]},
        }

        # Act
        result = replace_decimal_with_float(test_input)

        # Assert
        assert result == {
            "decimal": 10.5,
            "integer": 5,
            "list": [1.1, 2.2],
            "nested": {"a": 3.3, "b": [4.4]},
        }

    def test_replace_decimal_with_float_3(self):
        """
        Test replace_decimal_with_float function with Binary input
        """
        # Arrange
        binary_data = b"Hello, World!"
        binary_obj = Binary(binary_data)

        # Act
        result = replace_decimal_with_float(binary_obj)

        # Assert
        assert isinstance(result, bytes)
        assert result == binary_data

    def test_replace_decimal_with_float_4(self):
        """
        Test replace_decimal_with_float with a dictionary containing various types
        """
        # Prepare test data
        test_dict = {
            "int_key": 42,
            "float_key": 3.14,
            "decimal_key": Decimal("2.718"),
            "list_key": [Decimal("1.23"), 4, Decimal("5.67")],
            "nested_dict": {"nested_decimal": Decimal("9.876"), "nested_int": 100},
            "binary_key": Binary(b"test_binary"),
        }

        # Call the function
        result = replace_decimal_with_float(test_dict)

        # Assert the results
        assert isinstance(result, dict)
        assert result["int_key"] == 42
        assert result["float_key"] == 3.14
        assert result["decimal_key"] == 2.718
        assert result["list_key"] == [1.23, 4, 5.67]
        assert result["nested_dict"] == {"nested_decimal": 9.876, "nested_int": 100}
        assert result["binary_key"] == b"test_binary"

        # Check that all Decimal values have been converted
        assert all(not isinstance(v, Decimal) for v in result.values())
        assert all(not isinstance(v, Decimal) for v in result["list_key"])
        assert all(not isinstance(v, Decimal) for v in result["nested_dict"].values())

    def test_replace_decimal_with_float_5(self):
        """
        Test that replace_decimal_with_float returns the original object for various non-convertible types.
        """
        # Test cases with different non-convertible types
        test_cases = [
            42,  # int
            3.14,  # float
            True,  # boolean
            None,  # None
            (1, 2, 3),  # tuple
            set([1, 2, 3]),  # set
        ]

        for test_input in test_cases:
            # Act
            result = replace_decimal_with_float(test_input)

            # Assert
            assert (
                result == test_input
            ), f"Function should return the original object for {type(test_input)}"

    def test_replace_decimal_with_float_dict(self):
        """
        Test replace_decimal_with_float function with dict input
        """
        # Arrange
        dict_input = {
            "int": Decimal("10"),
            "float": Decimal("20.5"),
            "string": "value",
            "nested": {"decimal": Decimal("30")},
        }

        # Act
        result = replace_decimal_with_float(dict_input)

        # Assert
        assert isinstance(result, dict)
        assert result == {
            "int": 10,
            "float": 20.5,
            "string": "value",
            "nested": {"decimal": 30},
        }

    def test_replace_decimal_with_float_empty_input(self):
        """
        Test replace_decimal_with_float with empty input
        """
        assert replace_decimal_with_float([]) == []
        assert replace_decimal_with_float({}) == {}

    def test_replace_decimal_with_float_float(self):
        """
        Test replace_decimal_with_float function with Decimal input (float)
        """
        # Arrange
        decimal_input = Decimal("10.5")

        # Act
        result = replace_decimal_with_float(decimal_input)

        # Assert
        assert isinstance(result, float)
        assert result == 10.5

    def test_replace_decimal_with_float_integer(self):
        """
        Test replace_decimal_with_float function with Decimal input (integer)
        """
        # Arrange
        decimal_input = Decimal("10")

        # Act
        result = replace_decimal_with_float(decimal_input)

        # Assert
        assert isinstance(result, int)
        assert result == 10

    def test_replace_decimal_with_float_list(self):
        """
        Test replace_decimal_with_float function with list input
        """
        # Arrange
        list_input = [Decimal("10"), Decimal("20.5"), "string", [Decimal("30")]]

        # Act
        result = replace_decimal_with_float(list_input)

        # Assert
        assert isinstance(result, list)
        assert result == [10, 20.5, "string", [30]]

    def test_replace_decimal_with_float_list_input(self):
        """
        Test replace_decimal_with_float function with a list input containing Decimal values.
        """
        input_list = [Decimal("10.5"), Decimal("20"), [Decimal("30.75"), Decimal("40")]]
        expected_output = [10.5, 20, [30.75, 40]]

        result = replace_decimal_with_float(input_list)

        assert (
            result == expected_output
        ), f"Expected {expected_output}, but got {result}"
        assert all(
            isinstance(item, (int, float)) for item in result[:2]
        ), "Top-level items should be int or float"
        assert isinstance(result[2], list), "Nested item should be a list"
        assert all(
            isinstance(item, (int, float)) for item in result[2]
        ), "Nested list items should be int or float"

    def test_replace_decimal_with_float_nested_structure(self):
        """
        Test replace_decimal_with_float with a deeply nested structure
        """
        nested_input = {
            "a": [Decimal("1.5"), {"b": Decimal("2.0")}],
            "c": {"d": [Decimal("3.0"), Binary(b"test")]},
        }
        expected_output = {"a": [1.5, {"b": 2.0}], "c": {"d": [3, b"test"]}}
        assert replace_decimal_with_float(nested_input) == expected_output

    def test_replace_decimal_with_float_non_convertible_type(self):
        """
        Test that replace_decimal_with_float returns the original object when it's not a Decimal, list, Binary, or dict.
        """
        # Arrange
        test_input = "This is a string"

        # Act
        result = replace_decimal_with_float(test_input)

        # Assert
        assert (
            result == test_input
        ), "Function should return the original object for non-convertible types"

    def test_replace_decimal_with_float_non_decimal_types(self):
        """
        Test replace_decimal_with_float with non-Decimal types
        """
        input_data = [1, "string", True, None]
        assert replace_decimal_with_float(input_data) == input_data

    def test_replace_decimal_with_float_other(self):
        """
        Test replace_decimal_with_float function with other input types
        """
        # Arrange
        string_input = "test"
        int_input = 42
        float_input = 3.14

        # Act
        result_string = replace_decimal_with_float(string_input)
        result_int = replace_decimal_with_float(int_input)
        result_float = replace_decimal_with_float(float_input)

        # Assert
        assert result_string == "test"
        assert result_int == 42
        assert result_float == 3.14

    def test_replace_decimal_with_integer(self):
        """
        Test that replace_decimal_with_float converts a Decimal to an integer when it's a whole number.
        """
        # Arrange
        decimal_input = Decimal("5.0")

        # Act
        result = replace_decimal_with_float(decimal_input)

        # Assert
        assert isinstance(result, int)
        assert result == 5

    def test_replace_floats_with_decimal_converts_float_to_decimal(self):
        """
        Test that replace_floats_with_decimal converts a float to a Decimal
        with 4 decimal places, rounding down.
        """
        # Arrange
        input_float = 3.14159265359

        # Act
        result = replace_floats_with_decimal(input_float)

        # Assert
        expected = Decimal("3.1415").quantize(Decimal(".0001"), rounding=ROUND_DOWN)
        assert isinstance(result, Decimal)
        assert result == expected

    def test_replace_floats_with_decimal_dict(self):
        """
        Test replace_floats_with_decimal with a dictionary containing nested floats
        """
        input_dict = {
            "a": 1.23,
            "b": {"c": 4.56, "d": [7.89, 10.11]},
            "e": "string",
            "f": 12,
        }
        expected_output = {
            "a": Decimal("1.2300"),
            "b": {"c": Decimal("4.5600"), "d": [Decimal("7.8900"), Decimal("10.1100")]},
            "e": "string",
            "f": 12,
        }
        result = replace_floats_with_decimal(input_dict)
        assert result == expected_output
        assert isinstance(result["a"], Decimal)
        assert isinstance(result["b"]["c"], Decimal)
        assert isinstance(result["b"]["d"][0], Decimal)
        assert isinstance(result["b"]["d"][1], Decimal)
        assert isinstance(result["e"], str)
        assert isinstance(result["f"], int)

    def test_replace_floats_with_decimal_edge_cases(self):
        """
        Test replace_floats_with_decimal with edge cases
        """
        # Test with a mix of types
        mixed_input = [1, 2.0, "3", {"a": 4.5, "b": [5, 6.7]}]
        result = replace_floats_with_decimal(mixed_input)
        assert result == [
            1,
            Decimal("2.0000"),
            "3",
            {"a": Decimal("4.5000"), "b": [5, Decimal("6.7000")]},
        ]

        # Test with nested structures
        nested_input = {"a": [1.1, 2.2, {"b": 3.3, "c": [4.4, 5.5]}]}
        result = replace_floats_with_decimal(nested_input)
        assert isinstance(result["a"][0], Decimal)
        assert isinstance(result["a"][1], Decimal)
        assert isinstance(result["a"][2]["b"], Decimal)
        assert isinstance(result["a"][2]["c"][0], Decimal)
        assert isinstance(result["a"][2]["c"][1], Decimal)

        # Test with zero
        assert replace_floats_with_decimal(0.0) == Decimal("0.0000")

        # Test with negative numbers
        assert replace_floats_with_decimal(-1.5) == Decimal("-1.5000")

    def test_replace_floats_with_decimal_empty_input(self):
        """
        Test replace_floats_with_decimal with empty input
        """
        assert replace_floats_with_decimal([]) == []
        assert replace_floats_with_decimal({}) == {}

    def test_replace_floats_with_decimal_incorrect_format(self):
        """
        Test replace_floats_with_decimal with incorrect format in nested structures
        """
        incorrect_input = {"a": 1.5, "b": [2.5, {"c": 3.5, "d": "not a number"}]}
        result = replace_floats_with_decimal(incorrect_input)
        assert isinstance(result["a"], Decimal)
        assert isinstance(result["b"][0], Decimal)
        assert isinstance(result["b"][1]["c"], Decimal)
        assert result["b"][1]["d"] == "not a number"

    def test_replace_floats_with_decimal_list(self):
        """
        Test replace_floats_with_decimal function with a list input containing floats and other types.
        """
        input_list = [1.23, 4.56, "string", 7, [8.90, 10.11]]
        expected_output = [
            Decimal("1.2300"),
            Decimal("4.5600"),
            "string",
            7,
            [Decimal("8.9000"), Decimal("10.1100")],
        ]

        result = replace_floats_with_decimal(input_list)

        assert result == expected_output
        assert all(
            isinstance(item, Decimal)
            for item in result
            if isinstance(item, (Decimal, float))
        )
        assert isinstance(result[4], list)
        assert all(isinstance(subitem, Decimal) for subitem in result[4])

    def test_replace_floats_with_decimal_returns_non_float_list_dict_unchanged(self):
        """
        Test that replace_floats_with_decimal returns the input unchanged
        when it's not a float, list, or dict.
        """
        # Test with an integer
        assert replace_floats_with_decimal(42) == 42

        # Test with a string
        assert replace_floats_with_decimal("test") == "test"

        # Test with None
        assert replace_floats_with_decimal(None) is None

        # Test with a boolean
        assert replace_floats_with_decimal(True) is True

        # Test with a complex number
        complex_num = 1 + 2j
        assert replace_floats_with_decimal(complex_num) == complex_num
