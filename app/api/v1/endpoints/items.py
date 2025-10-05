"""
Items API endpoints

This module provides RESTful API endpoints for managing items.
All endpoints use Pydantic validation for request/response data
and delegate business logic to the ItemService layer.

Endpoints:
    GET    /items/           - List all items with optional filters
    GET    /items/{item_id}  - Get a specific item by ID
    POST   /items/           - Create a new item
    PUT    /items/{item_id}  - Update an existing item
    DELETE /items/{item_id}  - Delete an item
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.schemas.item import Item, ItemCreate, ItemUpdate
from app.services.item_service import ItemService, get_item_service

router = APIRouter()


@router.get("/", response_model=List[Item])
async def get_items(
    available_only: Optional[bool] = Query(
        None, description="Filter by availability status"
    ),
    min_price: Optional[float] = Query(
        None, ge=0, description="Minimum price filter"
    ),
    max_price: Optional[float] = Query(
        None, ge=0, description="Maximum price filter"
    ),
    search: Optional[str] = Query(
        None, min_length=1, max_length=100, description="Search by item name"
    ),
    item_service: ItemService = Depends(get_item_service),
):
    """
    Get all items with optional filters

    This endpoint retrieves all items from the system with support for
    multiple optional filters. Filters can be combined to narrow results.
    All query parameters are validated using Pydantic.

    Query Parameters:
        available_only (bool, optional): Filter by availability status.
            If True, returns only items where is_available=True.
        min_price (float, optional): Minimum price filter (inclusive).
            Must be >= 0. Validated by Pydantic.
        max_price (float, optional): Maximum price filter (inclusive).
            Must be >= 0. Validated by Pydantic.
        search (str, optional): Search term for item name (case-insensitive).
            Must be 1-100 characters. Validated by Pydantic.
        item_service (ItemService): Injected service dependency.

    Returns:
        List[Item]: List of items matching the filter criteria.
            Returns empty list if no items match.

    Example:
        GET /api/v1/items/?available_only=true&min_price=10&max_price=50
        GET /api/v1/items/?search=apple

    Status Codes:
        200: Success - Returns list of items
        422: Validation Error - Invalid query parameters
    """
    # Start with all items
    items = item_service.get_all_items()

    # Apply filters
    if available_only is not None and available_only:
        items = item_service.get_available_items()

    if min_price is not None and max_price is not None:
        items = item_service.get_items_by_price_range(min_price, max_price)
    elif min_price is not None:
        items = [item for item in items if item.price >= min_price]
    elif max_price is not None:
        items = [item for item in items if item.price <= max_price]

    if search is not None:
        items = item_service.search_items_by_name(search)

    return items


@router.get("/{item_id}", response_model=Item)
async def get_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to retrieve"),
    item_service: ItemService = Depends(get_item_service),
):
    """
    Get a specific item by ID

    Retrieves a single item from the system by its unique identifier.
    The item_id is validated to ensure it's a positive integer.

    Path Parameters:
        item_id (int): The unique identifier of the item to retrieve.
            Must be a positive integer (> 0). Validated by Pydantic.
        item_service (ItemService): Injected service dependency.

    Returns:
        Item: The requested item with all its properties.

    Raises:
        HTTPException:
            - 404 Not Found: If no item exists with the given ID
            - 422 Validation Error: If item_id is not a positive integer

    Example:
        GET /api/v1/items/1
        GET /api/v1/items/42

    Status Codes:
        200: Success - Returns the item
        404: Not Found - Item doesn't exist
        422: Validation Error - Invalid item_id
    """
    item = item_service.get_item_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=Item, status_code=201)
async def create_item(
    item: ItemCreate,
    item_service: ItemService = Depends(get_item_service),
):
    """
    Create a new item

    Creates a new item in the system with the provided data.
    All fields are validated using the ItemCreate Pydantic schema.
    A unique ID is automatically assigned to the new item.

    Request Body:
        item (ItemCreate): The item data to create. Required fields:
            - name (str): Item name (1-100 characters)
            - price (float): Item price (must be > 0)
            - description (str, optional): Item description (max 500 chars)
            - is_available (bool, optional): Availability status (default: True)
        item_service (ItemService): Injected service dependency.

    Returns:
        Item: The newly created item with assigned ID and all properties.

    Example Request Body:
        {
            "name": "Sample Item",
            "description": "A sample item description",
            "price": 29.99,
            "is_available": true
        }

    Status Codes:
        201: Created - Item successfully created
        422: Validation Error - Invalid request body
    """
    return item_service.create_item(item)


@router.put("/{item_id}", response_model=Item)
async def update_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to update"),
    item: ItemUpdate = ...,
    item_service: ItemService = Depends(get_item_service),
):
    """
    Update an existing item

    Updates an existing item with the provided data. Supports partial updates
    (only provided fields will be updated). All fields are validated using
    the ItemUpdate Pydantic schema.

    Path Parameters:
        item_id (int): The unique identifier of the item to update.
            Must be a positive integer (> 0). Validated by Pydantic.

    Request Body:
        item (ItemUpdate): The updated item data. All fields are optional:
            - name (str, optional): New item name (1-100 characters)
            - price (float, optional): New price (must be > 0)
            - description (str, optional): New description (max 500 chars)
            - is_available (bool, optional): New availability status
        item_service (ItemService): Injected service dependency.

    Returns:
        Item: The updated item with all current properties.

    Raises:
        HTTPException:
            - 404 Not Found: If no item exists with the given ID
            - 422 Validation Error: If item_id or request body is invalid

    Example Request Body:
        {
            "name": "Updated Name",
            "price": 39.99
        }

    Status Codes:
        200: Success - Item updated
        404: Not Found - Item doesn't exist
        422: Validation Error - Invalid data
    """
    updated_item = item_service.update_item(item_id, item)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to delete"),
    item_service: ItemService = Depends(get_item_service),
):
    """
    Delete an item

    Permanently deletes an item from the system by its unique identifier.
    This operation cannot be undone.

    Path Parameters:
        item_id (int): The unique identifier of the item to delete.
            Must be a positive integer (> 0). Validated by Pydantic.
        item_service (ItemService): Injected service dependency.

    Returns:
        None: No content returned on successful deletion.

    Raises:
        HTTPException:
            - 404 Not Found: If no item exists with the given ID
            - 422 Validation Error: If item_id is not a positive integer

    Example:
        DELETE /api/v1/items/1

    Status Codes:
        204: No Content - Item successfully deleted
        404: Not Found - Item doesn't exist
        422: Validation Error - Invalid item_id
    """
    success = item_service.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")

