# Modified by smalvy, 2026 — adapted for portfolio-project-1
import json

from unittest.mock import patch, MagicMock

from items import app


def test_post_items():
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}

    with patch("items.app.get_table", return_value = mock_table):
        event = {
            "body": "{\"name\": \"test item\", \"description\": \"test\"}",
            "httpMethod": "POST"
        }
        response = app.lambda_handler(event, {})
        assert response["statusCode"] == 201


def test_get_items():
    mock_table = MagicMock()
    mock_table.scan.return_value = {
        "Items": [
            {"id": "123", "name": "test item", "description": "test 1"},
            {"id": "456", "name": "test item 2", "description": "test 2"},
            {"id": "789", "name": "test item 3", "description": "test 3"},
        ]
    }

    with patch("items.app.get_table", return_value = mock_table):
        event = {
            "httpMethod": "GET"
        }
        response = app.lambda_handler(event, {})
        assert response["statusCode"] == 200


def test_post_item_missing_body():
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}

    with patch("items.app.get_table", return_value = mock_table):
        event = {
            "body": None,
            "httpMethod": "POST"
        }
        response = app.lambda_handler(event, {})
        assert response["statusCode"] == 400


def test_method_not_allowed():
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}

    with patch("items.app.get_table", return_value = mock_table):
        event = {
            "httpMethod": ""
        }
        response = app.lambda_handler(event, {})
        assert response["statusCode"] == 405
