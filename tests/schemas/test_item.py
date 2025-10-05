"""Tests for app/schemas/item.py - Item Pydantic models"""

import pytest
from pydantic import ValidationError

from app.schemas.item import Item, ItemCreate, ItemUpdate, ItemBase


class TestItemBase:
    """Test suite for ItemBase schema"""

    def test_item_base_valid(self):
        """Test creating valid ItemBase"""
        item = ItemBase(
            name="Test Item",
            description="Test description",
            price=29.99,
            is_available=True
        )
        assert item.name == "Test Item"
        assert item.description == "Test description"
        assert item.price == 29.99
        assert item.is_available is True

    def test_item_base_defaults(self):
        """Test ItemBase default values"""
        item = ItemBase(name="Test", price=10.0)
        assert item.is_available is True
        assert item.description is None

    def test_item_base_name_required(self):
        """Test that name is required"""
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(price=10.0)
        assert "name" in str(exc_info.value)

    def test_item_base_price_required(self):
        """Test that price is required"""
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(name="Test")
        assert "price" in str(exc_info.value)

    def test_item_base_price_positive(self):
        """Test that price must be positive"""
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(name="Test", price=0)
        assert "price" in str(exc_info.value).lower()

    def test_item_base_price_negative(self):
        """Test that price cannot be negative"""
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(name="Test", price=-10.0)
        assert "price" in str(exc_info.value).lower()

    def test_item_base_name_min_length(self):
        """Test that name must have minimum length"""
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(name="", price=10.0)
        assert "name" in str(exc_info.value).lower()

    def test_item_base_name_max_length(self):
        """Test that name cannot exceed maximum length"""
        long_name = "x" * 101  # Exceeds 100 character limit
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(name=long_name, price=10.0)
        assert "name" in str(exc_info.value).lower()

    def test_item_base_description_max_length(self):
        """Test that description cannot exceed maximum length"""
        long_description = "x" * 501  # Exceeds 500 character limit
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(name="Test", description=long_description, price=10.0)
        assert "description" in str(exc_info.value).lower()


class TestItemCreate:
    """Test suite for ItemCreate schema"""

    def test_item_create_valid(self):
        """Test creating valid ItemCreate"""
        item = ItemCreate(
            name="New Item",
            description="New description",
            price=49.99,
            is_available=False
        )
        assert item.name == "New Item"
        assert item.description == "New description"
        assert item.price == 49.99
        assert item.is_available is False

    def test_item_create_minimal(self):
        """Test ItemCreate with minimal required fields"""
        item = ItemCreate(name="Minimal Item", price=5.0)
        assert item.name == "Minimal Item"
        assert item.price == 5.0
        assert item.is_available is True
        assert item.description is None

    def test_item_create_inherits_validation(self):
        """Test that ItemCreate inherits validation from ItemBase"""
        with pytest.raises(ValidationError):
            ItemCreate(name="Test", price=-5.0)


class TestItemUpdate:
    """Test suite for ItemUpdate schema"""

    def test_item_update_all_fields(self):
        """Test ItemUpdate with all fields"""
        item = ItemUpdate(
            name="Updated Name",
            description="Updated description",
            price=99.99,
            is_available=False
        )
        assert item.name == "Updated Name"
        assert item.description == "Updated description"
        assert item.price == 99.99
        assert item.is_available is False

    def test_item_update_partial(self):
        """Test ItemUpdate with partial fields"""
        item = ItemUpdate(name="Updated Name")
        assert item.name == "Updated Name"
        assert item.description is None
        assert item.price is None
        assert item.is_available is None

    def test_item_update_empty(self):
        """Test ItemUpdate with no fields (all optional)"""
        item = ItemUpdate()
        assert item.name is None
        assert item.description is None
        assert item.price is None
        assert item.is_available is None

    def test_item_update_price_validation(self):
        """Test that ItemUpdate validates price when provided"""
        with pytest.raises(ValidationError) as exc_info:
            ItemUpdate(price=0)
        assert "price" in str(exc_info.value).lower()

    def test_item_update_name_validation(self):
        """Test that ItemUpdate validates name when provided"""
        with pytest.raises(ValidationError) as exc_info:
            ItemUpdate(name="")
        assert "name" in str(exc_info.value).lower()


class TestItem:
    """Test suite for Item schema (with ID)"""

    def test_item_valid(self):
        """Test creating valid Item"""
        item = Item(
            id=1,
            name="Test Item",
            description="Test description",
            price=29.99,
            is_available=True
        )
        assert item.id == 1
        assert item.name == "Test Item"
        assert item.description == "Test description"
        assert item.price == 29.99
        assert item.is_available is True

    def test_item_id_required(self):
        """Test that id is required for Item"""
        with pytest.raises(ValidationError) as exc_info:
            Item(name="Test", price=10.0)
        assert "id" in str(exc_info.value)

    def test_item_id_type(self):
        """Test that id must be an integer"""
        with pytest.raises(ValidationError) as exc_info:
            Item(id="not-an-int", name="Test", price=10.0)
        assert "id" in str(exc_info.value).lower()

    def test_item_model_config(self):
        """Test that Item has proper model configuration"""
        assert hasattr(Item, "model_config")
        config = Item.model_config
        assert config.get("from_attributes") is True
        assert "json_schema_extra" in config

    def test_item_example_in_schema(self):
        """Test that Item has example in schema"""
        config = Item.model_config
        example = config.get("json_schema_extra", {}).get("example")
        assert example is not None
        assert "id" in example
        assert "name" in example
        assert "price" in example

