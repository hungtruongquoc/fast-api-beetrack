"""Tests for app/api/v1/endpoints/items.py - Items API endpoints"""

import pytest
from fastapi.testclient import TestClient


class TestItemsAPI:
    """Test suite for Items API endpoints"""

    def test_get_empty_items_list(self, client: TestClient):
        """Test getting items when list is empty"""
        response = client.get("/api/v1/items/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_item(self, client: TestClient, sample_item):
        """Test creating a new item"""
        response = client.post("/api/v1/items/", json=sample_item)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_item["name"]
        assert data["description"] == sample_item["description"]
        assert data["price"] == sample_item["price"]
        assert data["is_available"] == sample_item["is_available"]
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_create_item_invalid_data(self, client: TestClient):
        """Test creating item with invalid data"""
        invalid_item = {
            "name": "Test",
            "price": -10,  # Invalid: negative price
        }
        response = client.post("/api/v1/items/", json=invalid_item)
        assert response.status_code == 422  # Unprocessable Entity

    def test_create_item_missing_required_fields(self, client: TestClient):
        """Test creating item with missing required fields"""
        incomplete_item = {
            "name": "Test Item"
            # Missing required 'price' field
        }
        response = client.post("/api/v1/items/", json=incomplete_item)
        assert response.status_code == 422

    def test_get_item_by_id(self, client: TestClient, sample_item):
        """Test getting a specific item by ID"""
        # First create an item
        create_response = client.post("/api/v1/items/", json=sample_item)
        created_item = create_response.json()
        item_id = created_item["id"]

        # Then retrieve it
        response = client.get(f"/api/v1/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == sample_item["name"]

    def test_get_nonexistent_item(self, client: TestClient):
        """Test getting an item that doesn't exist"""
        response = client.get("/api/v1/items/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_item(self, client: TestClient, sample_item, sample_item_update):
        """Test updating an existing item"""
        # Create an item
        create_response = client.post("/api/v1/items/", json=sample_item)
        item_id = create_response.json()["id"]

        # Update it
        response = client.put(f"/api/v1/items/{item_id}", json=sample_item_update)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == sample_item_update["name"]
        assert data["price"] == sample_item_update["price"]
        assert data["is_available"] == sample_item_update["is_available"]

    def test_update_nonexistent_item(self, client: TestClient, sample_item_update):
        """Test updating an item that doesn't exist"""
        response = client.put("/api/v1/items/99999", json=sample_item_update)
        assert response.status_code == 404

    def test_partial_update_item(self, client: TestClient, sample_item):
        """Test partial update of an item"""
        # Create an item
        create_response = client.post("/api/v1/items/", json=sample_item)
        item_id = create_response.json()["id"]

        # Partially update it (only price)
        partial_update = {"price": 199.99}
        response = client.put(f"/api/v1/items/{item_id}", json=partial_update)
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 199.99
        assert data["name"] == sample_item["name"]  # Should remain unchanged

    def test_delete_item(self, client: TestClient, sample_item):
        """Test deleting an item"""
        # Create an item
        create_response = client.post("/api/v1/items/", json=sample_item)
        item_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/api/v1/items/{item_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_item(self, client: TestClient):
        """Test deleting an item that doesn't exist"""
        response = client.delete("/api/v1/items/99999")
        assert response.status_code == 404

    def test_get_all_items(self, client: TestClient, sample_item):
        """Test getting all items after creating multiple"""
        # Create multiple items
        item1 = sample_item.copy()
        item1["name"] = "Item 1"
        item2 = sample_item.copy()
        item2["name"] = "Item 2"
        item3 = sample_item.copy()
        item3["name"] = "Item 3"

        client.post("/api/v1/items/", json=item1)
        client.post("/api/v1/items/", json=item2)
        client.post("/api/v1/items/", json=item3)

        # Get all items
        response = client.get("/api/v1/items/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all(isinstance(item["id"], int) for item in data)


class TestItemValidation:
    """Test suite for item data validation at API level"""

    def test_item_name_too_long(self, client: TestClient):
        """Test that item name cannot exceed max length"""
        long_name = "x" * 101  # Exceeds 100 character limit
        item = {
            "name": long_name,
            "price": 10.0,
        }
        response = client.post("/api/v1/items/", json=item)
        assert response.status_code == 422

    def test_item_name_empty(self, client: TestClient):
        """Test that item name cannot be empty"""
        item = {
            "name": "",
            "price": 10.0,
        }
        response = client.post("/api/v1/items/", json=item)
        assert response.status_code == 422

    def test_item_price_zero(self, client: TestClient):
        """Test that item price must be greater than zero"""
        item = {
            "name": "Test Item",
            "price": 0,
        }
        response = client.post("/api/v1/items/", json=item)
        assert response.status_code == 422

    def test_item_description_optional(self, client: TestClient):
        """Test that description is optional"""
        item = {
            "name": "Test Item",
            "price": 10.0,
        }
        response = client.post("/api/v1/items/", json=item)
        assert response.status_code == 201
        data = response.json()
        assert data["description"] is None

    def test_item_is_available_default(self, client: TestClient):
        """Test that is_available defaults to True"""
        item = {
            "name": "Test Item",
            "price": 10.0,
        }
        response = client.post("/api/v1/items/", json=item)
        assert response.status_code == 201
        data = response.json()
        assert data["is_available"] is True

    def test_item_price_type_validation(self, client: TestClient):
        """Test that price must be a number"""
        item = {
            "name": "Test Item",
            "price": "not-a-number",
        }
        response = client.post("/api/v1/items/", json=item)
        assert response.status_code == 422

    def test_item_is_available_type_validation(self, client: TestClient):
        """Test that is_available must be a boolean"""
        item = {
            "name": "Test Item",
            "price": 10.0,
            "is_available": "not-a-boolean",
        }
        response = client.post("/api/v1/items/", json=item)
        assert response.status_code == 422

