"""
Item service for business logic

This module contains the ItemService class which handles all business logic
for item operations. It follows the service layer pattern, separating
business logic from API endpoints.

The service uses in-memory storage (dictionary) for demonstration purposes.
In production, this should be replaced with a proper database layer using
SQLAlchemy or similar ORM.

Architecture:
    API Layer (endpoints) → Service Layer (this file) → Data Layer (future: database)

Classes:
    ItemService: Main service class for item operations

Functions:
    get_item_service: Factory function returning singleton instance
"""

from typing import List, Optional

from app.schemas.item import Item, ItemCreate, ItemUpdate
from app.core.logging import get_logger


class ItemService:
    """
    Service class for item business logic

    This class encapsulates all business logic related to item operations.
    It provides methods for CRUD operations, filtering, and searching items.

    The service uses in-memory storage (dictionary) for demonstration.
    In production, replace this with database operations using SQLAlchemy.

    Attributes:
        _items_db (dict[int, Item]): In-memory storage for items
        _next_id (int): Counter for generating unique IDs

    Methods:
        CRUD Operations:
            - create_item: Create a new item
            - get_all_items: Retrieve all items
            - get_item_by_id: Retrieve a specific item
            - update_item: Update an existing item
            - delete_item: Delete an item

        Utility Methods:
            - item_exists: Check if item exists
            - get_items_count: Get total count of items
            - clear_all_items: Clear all items (for testing)

        Filtering Methods:
            - get_available_items: Get only available items
            - get_items_by_price_range: Filter by price range
            - search_items_by_name: Search by name (case-insensitive)
    """

    def __init__(self):
        """
        Initialize the service with in-memory storage

        Creates empty dictionary for storing items and initializes
        the ID counter to 1.
        """
        self._items_db: dict[int, Item] = {}
        self._next_id: int = 1
        self.logger = get_logger(__name__)

    def get_all_items(self) -> List[Item]:
        """
        Get all items from storage
        
        Returns:
            List[Item]: List of all items
        """
        items = list(self._items_db.values())
        self.logger.debug("Retrieved all items", total_items=len(items))
        return items

    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        """
        Get a specific item by ID
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            Optional[Item]: The item if found, None otherwise
        """
        item = self._items_db.get(item_id)
        if item:
            self.logger.debug("Item retrieved", item_id=item_id, item_name=item.name)
        else:
            self.logger.debug("Item not found", item_id=item_id)
        return item

    def create_item(self, item_data: ItemCreate) -> Item:
        """
        Create a new item
        
        Args:
            item_data: The item data to create
            
        Returns:
            Item: The newly created item with assigned ID
        """
        new_item = Item(id=self._next_id, **item_data.model_dump())
        self._items_db[self._next_id] = new_item
        self.logger.info(
            "Item created",
            item_id=self._next_id,
            item_name=new_item.name,
            item_price=new_item.price,
            is_available=new_item.is_available
        )
        self._next_id += 1
        return new_item

    def update_item(self, item_id: int, item_data: ItemUpdate) -> Optional[Item]:
        """
        Update an existing item
        
        Args:
            item_id: The ID of the item to update
            item_data: The updated item data
            
        Returns:
            Optional[Item]: The updated item if found, None otherwise
        """
        if item_id not in self._items_db:
            self.logger.warning("Item update failed - item not found", item_id=item_id)
            return None
        
        stored_item = self._items_db[item_id]
        update_data = item_data.model_dump(exclude_unset=True)
        updated_item = stored_item.model_copy(update=update_data)
        self._items_db[item_id] = updated_item
        
        self.logger.info(
            "Item updated",
            item_id=item_id,
            item_name=updated_item.name,
            updated_fields=list(update_data.keys())
        )
        return updated_item

    def delete_item(self, item_id: int) -> bool:
        """
        Delete an item
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            bool: True if item was deleted, False if not found
        """
        if item_id not in self._items_db:
            self.logger.warning("Item deletion failed - item not found", item_id=item_id)
            return False
        
        item_name = self._items_db[item_id].name
        del self._items_db[item_id]
        self.logger.info("Item deleted", item_id=item_id, item_name=item_name)
        return True

    def item_exists(self, item_id: int) -> bool:
        """
        Check if an item exists
        
        Args:
            item_id: The ID of the item to check
            
        Returns:
            bool: True if item exists, False otherwise
        """
        return item_id in self._items_db

    def get_items_count(self) -> int:
        """
        Get the total count of items
        
        Returns:
            int: Total number of items
        """
        return len(self._items_db)

    def clear_all_items(self) -> None:
        """
        Clear all items from storage (useful for testing)
        """
        self._items_db.clear()
        self._next_id = 1

    def get_available_items(self) -> List[Item]:
        """
        Get all available items
        
        Returns:
            List[Item]: List of items where is_available is True
        """
        available_items = [item for item in self._items_db.values() if item.is_available]
        self.logger.debug(
            "Retrieved available items",
            available_count=len(available_items),
            total_count=len(self._items_db)
        )
        return available_items

    def get_items_by_price_range(
        self, min_price: float, max_price: float
    ) -> List[Item]:
        """
        Get items within a price range
        
        Args:
            min_price: Minimum price (inclusive)
            max_price: Maximum price (inclusive)
            
        Returns:
            List[Item]: List of items within the price range
        """
        filtered_items = [
            item
            for item in self._items_db.values()
            if min_price <= item.price <= max_price
        ]
        self.logger.debug(
            "Filtered items by price range",
            min_price=min_price,
            max_price=max_price,
            filtered_count=len(filtered_items),
            total_count=len(self._items_db)
        )
        return filtered_items

    def search_items_by_name(self, search_term: str) -> List[Item]:
        """
        Search items by name (case-insensitive)
        
        Args:
            search_term: The search term to match against item names
            
        Returns:
            List[Item]: List of items matching the search term
        """
        search_term_lower = search_term.lower()
        matching_items = [
            item
            for item in self._items_db.values()
            if search_term_lower in item.name.lower()
        ]
        self.logger.debug(
            "Searched items by name",
            search_term=search_term,
            matching_count=len(matching_items),
            total_count=len(self._items_db)
        )
        return matching_items


# Singleton instance for the application
# In a real application, you might use dependency injection instead
_item_service_instance: Optional[ItemService] = None


def get_item_service() -> ItemService:
    """
    Get the singleton instance of ItemService
    
    This function can be used as a FastAPI dependency
    
    Returns:
        ItemService: The item service instance
    """
    global _item_service_instance
    if _item_service_instance is None:
        _item_service_instance = ItemService()
    return _item_service_instance

