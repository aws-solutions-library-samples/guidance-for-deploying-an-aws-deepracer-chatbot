import os
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import boto3
import pytest
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from moto import mock_aws, settings
from utils.model_storage import ModelStorage


class TestModelStorage:

    @pytest.fixture(autouse=True)
    def aws_credentials(self):
        """Mocked AWS Credentials for moto."""
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    @pytest.fixture
    def model_storage(self):
        return ModelStorage("test_table")

    @pytest.fixture
    def mock_dynamodb_table(self, aws_credentials):
        """Fixture to create a mock DynamoDB table"""
        with mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
            table = dynamodb.create_table(
                TableName="test_table",
                KeySchema=[
                    {"AttributeName": "userId", "KeyType": "HASH"},
                    {"AttributeName": "modelName", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "userId", "AttributeType": "S"},
                    {"AttributeName": "modelName", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            yield table

    @mock_aws
    def test___init___2(self):
        """
        Test initialization of ModelStorage without providing a boto3 session
        """
        # Arrange
        table_name = "test-table"

        # Create a mock DynamoDB table
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "modelName", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "modelName", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Act
        model_storage = ModelStorage(table_name)

        # Assert
        assert model_storage.ddbTable.name == table_name
        assert isinstance(model_storage.ddbTable, boto3.resources.base.ServiceResource)

    @mock_aws
    def test___init___with_custom_session(self):
        """
        Test initialization of ModelStorage with a custom boto3 session
        """
        # Set up mock DynamoDB table
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="TestTable",
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "modelName", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "modelName", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create a custom boto3 session
        custom_session = boto3.Session(region_name="us-east-1")

        # Initialize ModelStorage with custom session
        model_storage = ModelStorage("TestTable", boto3_session=custom_session)

        # Assert that the DynamoDB table is correctly initialized
        assert model_storage.ddbTable.name == "TestTable"
        assert model_storage.ddbTable.meta.client.meta.region_name == "us-east-1"

        # Verify that the table exists
        table = dynamodb.Table("TestTable")
        assert table.table_status == "ACTIVE"

    def test_add_model_success(self, mock_dynamodb_table):
        """
        Test successful addition of a model to DynamoDB.
        """
        # Mock the DynamoDB table
        mock_table = Mock()
        mock_table.update_item.return_value = {
            "Attributes": {
                "userId": "test_user",
                "modelName": "test_model",
                "data": "test_data",
            }
        }

        # Create ModelStorage instance with mocked table
        model_storage = ModelStorage("test_table")
        model_storage.ddbTable = mock_table

        # Test data
        user_id = "test_user"
        model_name = "test_model"
        model_data = {"data": "test_data"}

        # Call the method
        result = model_storage.add_model(user_id, model_name, model_data)

        # Assertions
        assert result == {
            "userId": "test_user",
            "modelName": "test_model",
            "data": "test_data",
        }
        mock_table.update_item.assert_called_once()

    def test_get_model_2(self, mock_dynamodb_table):
        """
        Test get_model when the item is not found in DynamoDB.
        """
        # Create a mock DynamoDB table
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table_name = "test-table"
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "modelName", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "modelName", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Initialize ModelStorage with mock table
        model_storage = ModelStorage(table_name)

        # Test get_model with non-existent item
        user_id = "test_user"
        model_name = "non_existent_model"
        result = model_storage.get_model(user_id, model_name)

        # Assert that the result is None when item is not found
        assert result is None

    def test_get_model_client_error(self, mock_dynamodb_table):
        """
        Test get_model when ClientError is raised
        """
        model_storage = ModelStorage("test_table")
        model_storage.ddbTable.get_item = lambda **kwargs: (_ for _ in ()).throw(
            ClientError({}, "")
        )

        with pytest.raises(ClientError):
            model_storage.get_model("user_id", "model_name")

    def test_get_model_no_item_found(self, mock_dynamodb_table):
        """
        Test get_model when no item is found
        """
        model_storage = ModelStorage("test_table")
        model_storage.ddbTable.get_item = lambda **kwargs: {"ResponseMetadata": {}}

        result = model_storage.get_model("user_id", "model_name")
        assert result is None

    def test_get_model_when_client_error_occurs(self, mock_dynamodb_table):
        """
        Test get_model method when a ClientError occurs
        """
        # Mock the DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.side_effect = ClientError(
            error_response={
                "Error": {"Code": "TestException", "Message": "Test error message"}
            },
            operation_name="GetItem",
        )

        # Create ModelStorage instance with mocked table
        model_storage = ModelStorage("test_table")
        model_storage.ddbTable = mock_table

        # Call the method and assert that it raises a ClientError
        with pytest.raises(ClientError):
            model_storage.get_model("test_user", "test_model")

        # Verify that get_item was called with correct parameters
        mock_table.get_item.assert_called_once_with(
            Key={"userId": "test_user", "modelName": "test_model"}
        )

    def test_get_model_when_item_does_not_exist(self, mock_dynamodb_table):
        """
        Test get_model method when an item does not exist in DynamoDB
        """
        # Mock the DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}

        # Create ModelStorage instance with mocked table
        model_storage = ModelStorage("test_table")
        model_storage.ddbTable = mock_table

        # Call the method
        result = model_storage.get_model("test_user", "test_model")

        # Assert the result
        assert result is None

        # Verify that get_item was called with correct parameters
        mock_table.get_item.assert_called_once_with(
            Key={"userId": "test_user", "modelName": "test_model"}
        )

    def test_get_model_when_item_exists(self, mock_dynamodb_table):
        """
        Test get_model method when an item exists in DynamoDB
        """
        # Mock the DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "userId": "test_user",
                "modelName": "test_model",
                "value": Decimal("10.5"),
            }
        }

        # Create ModelStorage instance with mocked table
        model_storage = ModelStorage("test_table")
        model_storage.ddbTable = mock_table

        # Call the method
        result = model_storage.get_model("test_user", "test_model")

        # Assert the result
        assert result == {
            "userId": "test_user",
            "modelName": "test_model",
            "value": 10.5,
        }

        # Verify that get_item was called with correct parameters
        mock_table.get_item.assert_called_once_with(
            Key={"userId": "test_user", "modelName": "test_model"}
        )

    def test_get_model_with_empty_inputs(self, mock_dynamodb_table):
        """
        Test get_model with empty user_id and model_name
        """
        model_storage = ModelStorage("test_table")
        with pytest.raises(ClientError):
            model_storage.get_model("", "")

    def test_init_with_empty_table_name(self):
        """
        Test initialization with an empty table name.
        """
        with pytest.raises(ValueError):
            ModelStorage("")

    def test_init_with_invalid_boto3_session(self):
        """
        Test initialization with an invalid boto3 session.
        """
        with pytest.raises(AttributeError):
            ModelStorage("valid_table", boto3_session="invalid_session")

    def test_init_with_non_existent_table(self, mock_dynamodb_table):
        """
        Test initialization with a non-existent table name.
        """
        with pytest.raises(ClientError):
            ModelStorage("non_existent_table")

    def test_list_models_1(self):
        # Existing test method, left unchanged
        pass

    @mock_aws
    def test_list_models_2(self):
        """
        Test list_models when there are models for the given user.
        """
        # Set up DynamoDB mock
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table_name = "TestModelTable"
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "modelName", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "modelName", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create ModelStorage instance
        model_storage = ModelStorage(table_name)

        # Add test data
        user_id = "test_user"
        models = [
            {"userId": user_id, "modelName": "model1"},
            {"userId": user_id, "modelName": "model2"},
            {"userId": user_id, "modelName": "model3"},
        ]
        with table.batch_writer() as batch:
            for model in models:
                batch.put_item(Item=model)

        # Call the method under test
        result = model_storage.list_models(user_id)

        # Assert the result
        expected_result = {"Models": ["model1", "model2", "model3"]}
        assert (
            result == expected_result
        ), f"Expected {expected_result}, but got {result}"

    def test_list_models_empty(self, mock_dynamodb_table):
        """
        Test list_models when no models exist for the user.
        Expected to return an empty list of models.
        """
        # Set up mock DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table_name = "TestModelTable"
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "modelName", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "modelName", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Initialize ModelStorage with mock table
        model_storage = ModelStorage(table_name)

        # Test list_models for a user with no models
        user_id = "test_user"
        result = model_storage.list_models(user_id)

        # Assert the result
        assert result == {"Models": []}

    def test_list_models_empty_user_id(self, mock_dynamodb_table):
        """
        Test list_models with an empty user_id.
        """
        model_storage = ModelStorage("test_table")
        result = model_storage.list_models("")
        assert "Error" in result
        assert "Error listing models" in result["Error"]
