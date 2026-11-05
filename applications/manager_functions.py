"""Compatibility wrappers. Catalog changes live in applications.catalog."""

from applications.catalog import (
    add_category as add_category_to_db,
    add_product as add_product_to_category_in_db,
    categories_with_products as get_categories_with_products_from_db,
    delete_category as remove_category_from_db,
    delete_product as remove_product_from_db,
    update_product as update_product_in_db,
)

__all__ = [
    "add_category_to_db",
    "add_product_to_category_in_db",
    "get_categories_with_products_from_db",
    "remove_category_from_db",
    "remove_product_from_db",
    "update_product_in_db",
]
