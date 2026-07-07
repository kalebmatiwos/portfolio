from datetime import datetime
from decimal import Decimal

from ETL.transform import (
    format_money,
    format_timestamp,
    normalise_data,
    parse_items_ordered,
    remove_sensitive_data,
    etl_transform,
)


def raw_rows():
    return [
        {
            "timestamp": "28/03/2025 09:00",
            "location": "Leeds",
            "customer name": "Ada Lovelace",
            "items ordered": "Latte - 3.50, Latte - 3.50, Tea - 2.00",
            "total amount": "9.00",
            "payment method": "card",
            "card number": "1234567890123456",
        },
        {
            "timestamp": "28/03/2025 09:10",
            "location": "Leeds",
            "customer name": "Grace Hopper",
            "items ordered": "Mocha - 4.25",
            "total amount": "4.25",
            "payment method": "cash",
            "card number": "",
        },
    ]


def test_remove_sensitive_data_drops_customer_name_and_card_number():
    cleaned_rows = remove_sensitive_data(raw_rows())

    assert "customer name" not in cleaned_rows[0]
    assert "card number" not in cleaned_rows[0]
    assert cleaned_rows[0] == {
        "timestamp": "28/03/2025 09:00",
        "location": "Leeds",
        "items ordered": "Latte - 3.50, Latte - 3.50, Tea - 2.00",
        "total amount": "9.00",
        "payment method": "card",
    }


def test_parse_items_ordered_splits_name_price_and_counts_duplicates():
    items = parse_items_ordered("Latte - 3.50, Latte - 3.50, Tea - 2.00")

    assert items == [
        {
            "product_name": "Latte",
            "quantity": 2,
            "unit_price": Decimal("3.50"),
        },
        {
            "product_name": "Tea",
            "quantity": 1,
            "unit_price": Decimal("2.00"),
        },
    ]


def test_format_helpers_return_database_friendly_types():
    assert format_money("3.5") == Decimal("3.50")
    assert format_timestamp("28/03/2025 09:00") == datetime(2025, 3, 28, 9, 0)


def test_normalise_data_shapes_rows_for_schema_and_preserves_foreign_keys():
    cleaned_rows = remove_sensitive_data(raw_rows())
    transformed = normalise_data(cleaned_rows)

    assert set(transformed) == {
        "branches",
        "payment_types",
        "products",
        "transactions",
        "transaction_items",
    }
    assert len(transformed["branches"]) == 1
    assert len(transformed["payment_types"]) == 2
    assert len(transformed["products"]) == 3
    assert len(transformed["transactions"]) == 2
    assert len(transformed["transaction_items"]) == 3

    branch_ids = {branch["branch_id"] for branch in transformed["branches"]}
    payment_method_ids = {
        payment_type["payment_method_id"]
        for payment_type in transformed["payment_types"]
    }
    product_ids = {product["product_id"] for product in transformed["products"]}
    transaction_ids = {
        transaction["transaction_id"]
        for transaction in transformed["transactions"]
    }

    for transaction in transformed["transactions"]:
        assert transaction["branch_id"] in branch_ids
        assert transaction["payment_method_id"] in payment_method_ids

    for item in transformed["transaction_items"]:
        assert item["transaction_id"] in transaction_ids
        assert item["product_id"] in product_ids


def test_transform_does_not_return_sensitive_customer_fields():
    transformed = etl_transform(raw_rows())
    all_output_rows = [
        row
        for table_rows in transformed.values()
        for row in table_rows
    ]

    assert all("customer name" not in row for row in all_output_rows)
    assert all("card number" not in row for row in all_output_rows)
