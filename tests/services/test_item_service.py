"""Tests for app/services/item_service.py - Item service business logic"""

import pytest

from app.schemas.item import ItemCreate, ItemUpdate
from app.services.item_service import ItemService


@pytest.fixture
def item_service():
    """Create a fresh ItemService instance for each test"""
    return ItemService()


@pytest.fixture
def sample_item_data():
    """Sample item data for testing"""
    return {
        "name": "Test Item",
        "description": "Test description",
        "price": 29.99,
        "is_available": True,
    }


class TestItemServiceBasicOperations:
    """Test suite for basic CRUD operations"""

    def test_create_item(self, item_service, sample_item_data):
        """Test creating a new item"""
        item_create = ItemCreate(**sample_item_data)
        item = item_service.create_item(item_create)

        assert item.id == 1
        assert item.name == sample_item_data["name"]
        assert item.description == sample_item_data["description"]
        assert item.price == sample_item_data["price"]
        assert item.is_available == sample_item_data["is_available"]

    def test_create_multiple_items_increments_id(self, item_service, sample_item_data):
        """Test that creating multiple items increments the ID"""
        item1 = item_service.create_item(ItemCreate(**sample_item_data))
        item2 = item_service.create_item(ItemCreate(**sample_item_data))
        item3 = item_service.create_item(ItemCreate(**sample_item_data))

        assert item1.id == 1
        assert item2.id == 2
        assert item3.id == 3

    def test_get_all_items_empty(self, item_service):
        """Test getting all items when storage is empty"""
        items = item_service.get_all_items()
        assert items == []

    def test_get_all_items(self, item_service, sample_item_data):
        """Test getting all items"""
        item_service.create_item(ItemCreate(**sample_item_data))
        item_service.create_item(ItemCreate(**sample_item_data))

        items = item_service.get_all_items()
        assert len(items) == 2

    def test_get_item_by_id(self, item_service, sample_item_data):
        """Test getting a specific item by ID"""
        created_item = item_service.create_item(ItemCreate(**sample_item_data))
        retrieved_item = item_service.get_item_by_id(created_item.id)

        assert retrieved_item is not None
        assert retrieved_item.id == created_item.id
        assert retrieved_item.name == created_item.name

    def test_get_item_by_id_not_found(self, item_service):
        """Test getting an item that doesn't exist"""
        item = item_service.get_item_by_id(999)
        assert item is None

    def test_update_item(self, item_service, sample_item_data):
        """Test updating an existing item"""
        created_item = item_service.create_item(ItemCreate(**sample_item_data))

        update_data = ItemUpdate(name="Updated Name", price=49.99)
        updated_item = item_service.update_item(created_item.id, update_data)

        assert updated_item is not None
        assert updated_item.id == created_item.id
        assert updated_item.name == "Updated Name"
        assert updated_item.price == 49.99
        assert updated_item.description == sample_item_data["description"]

    def test_update_item_partial(self, item_service, sample_item_data):
        """Test partial update of an item"""
        created_item = item_service.create_item(ItemCreate(**sample_item_data))

        update_data = ItemUpdate(price=99.99)
        updated_item = item_service.update_item(created_item.id, update_data)

        assert updated_item is not None
        assert updated_item.price == 99.99
        assert updated_item.name == sample_item_data["name"]

    def test_update_item_not_found(self, item_service):
        """Test updating an item that doesn't exist"""
        update_data = ItemUpdate(name="Updated")
        result = item_service.update_item(999, update_data)
        assert result is None

    def test_delete_item(self, item_service, sample_item_data):
        """Test deleting an item"""
        created_item = item_service.create_item(ItemCreate(**sample_item_data))

        success = item_service.delete_item(created_item.id)
        assert success is True

        # Verify item is deleted
        item = item_service.get_item_by_id(created_item.id)
        assert item is None

    def test_delete_item_not_found(self, item_service):
        """Test deleting an item that doesn't exist"""
        success = item_service.delete_item(999)
        assert success is False


class TestItemServiceUtilityMethods:
    """Test suite for utility methods"""

    def test_item_exists(self, item_service, sample_item_data):
        """Test checking if an item exists"""
        created_item = item_service.create_item(ItemCreate(**sample_item_data))

        assert item_service.item_exists(created_item.id) is True
        assert item_service.item_exists(999) is False

    def test_get_items_count(self, item_service, sample_item_data):
        """Test getting the count of items"""
        assert item_service.get_items_count() == 0

        item_service.create_item(ItemCreate(**sample_item_data))
        assert item_service.get_items_count() == 1

        item_service.create_item(ItemCreate(**sample_item_data))
        assert item_service.get_items_count() == 2

    def test_clear_all_items(self, item_service, sample_item_data):
        """Test clearing all items"""
        item_service.create_item(ItemCreate(**sample_item_data))
        item_service.create_item(ItemCreate(**sample_item_data))

        assert item_service.get_items_count() == 2

        item_service.clear_all_items()

        assert item_service.get_items_count() == 0
        assert item_service.get_all_items() == []

    def test_clear_all_items_resets_id(self, item_service, sample_item_data):
        """Test that clearing items resets the ID counter"""
        item_service.create_item(ItemCreate(**sample_item_data))
        item_service.create_item(ItemCreate(**sample_item_data))

        item_service.clear_all_items()

        new_item = item_service.create_item(ItemCreate(**sample_item_data))
        assert new_item.id == 1


class TestItemServiceFilteringMethods:
    """Test suite for filtering and search methods"""

    def test_get_available_items(self, item_service):
        """Test getting only available items"""
        item_service.create_item(
            ItemCreate(name="Available 1", price=10.0, is_available=True)
        )
        item_service.create_item(
            ItemCreate(name="Unavailable", price=20.0, is_available=False)
        )
        item_service.create_item(
            ItemCreate(name="Available 2", price=30.0, is_available=True)
        )

        available_items = item_service.get_available_items()

        assert len(available_items) == 2
        assert all(item.is_available for item in available_items)

    def test_get_items_by_price_range(self, item_service):
        """Test getting items within a price range"""
        item_service.create_item(ItemCreate(name="Cheap", price=10.0))
        item_service.create_item(ItemCreate(name="Medium", price=50.0))
        item_service.create_item(ItemCreate(name="Expensive", price=100.0))

        items = item_service.get_items_by_price_range(20.0, 80.0)

        assert len(items) == 1
        assert items[0].name == "Medium"

    def test_get_items_by_price_range_inclusive(self, item_service):
        """Test that price range is inclusive"""
        item_service.create_item(ItemCreate(name="Item 1", price=10.0))
        item_service.create_item(ItemCreate(name="Item 2", price=50.0))
        item_service.create_item(ItemCreate(name="Item 3", price=100.0))

        items = item_service.get_items_by_price_range(10.0, 100.0)

        assert len(items) == 3

    def test_search_items_by_name(self, item_service):
        """Test searching items by name"""
        item_service.create_item(ItemCreate(name="Apple Juice", price=5.0))
        item_service.create_item(ItemCreate(name="Orange Juice", price=6.0))
        item_service.create_item(ItemCreate(name="Apple Pie", price=10.0))

        items = item_service.search_items_by_name("apple")

        assert len(items) == 2
        assert all("apple" in item.name.lower() for item in items)

    def test_search_items_by_name_case_insensitive(self, item_service):
        """Test that name search is case-insensitive"""
        item_service.create_item(ItemCreate(name="UPPERCASE", price=10.0))
        item_service.create_item(ItemCreate(name="lowercase", price=20.0))
        item_service.create_item(ItemCreate(name="MixedCase", price=30.0))

        items_upper = item_service.search_items_by_name("CASE")
        items_lower = item_service.search_items_by_name("case")

        assert len(items_upper) == 3
        assert len(items_lower) == 3

    def test_search_items_by_name_no_results(self, item_service):
        """Test searching with no matching results"""
        item_service.create_item(ItemCreate(name="Item 1", price=10.0))

        items = item_service.search_items_by_name("nonexistent")

        assert len(items) == 0


class TestItemServiceSingleton:
    """Test suite for singleton pattern"""

    def test_get_item_service_returns_same_instance(self):
        """Test that get_item_service returns the same instance"""
        from app.services.item_service import get_item_service

        service1 = get_item_service()
        service2 = get_item_service()

        assert service1 is service2

    def test_singleton_persists_data(self):
        """Test that singleton instance persists data across calls"""
        from app.services.item_service import get_item_service

        service1 = get_item_service()
        service1.create_item(ItemCreate(name="Test", price=10.0))

        service2 = get_item_service()
        items = service2.get_all_items()

        # Note: This test might fail if other tests have modified the singleton
        # In a real application, you'd want to reset the singleton between tests
        assert len(items) >= 1

