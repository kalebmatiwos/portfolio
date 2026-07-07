from decimal import Decimal

import ETL.load as load


class FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def transformed_data():
    branch_id = "00000000-0000-0000-0000-000000000001"
    payment_method_id = "00000000-0000-0000-0000-000000000002"
    product_id = "00000000-0000-0000-0000-000000000003"
    transaction_id = "00000000-0000-0000-0000-000000000004"

    return {
        "branches": [
            {
                "branch_id": branch_id,
                "branch_name": "Leeds",
            }
        ],
        "payment_types": [
            {
                "payment_method_id": payment_method_id,
                "payment_method": "card",
            }
        ],
        "products": [
            {
                "product_id": product_id,
                "product_name": "Latte",
                "current_price": Decimal("3.50"),
            }
        ],
        "transactions": [
            {
                "transaction_id": transaction_id,
                "branch_id": branch_id,
                "payment_method_id": payment_method_id,
                "transaction_timestamp": "2025-03-28 09:00:00",
                "transaction_total": Decimal("3.50"),
            }
        ],
        "transaction_items": [
            {
                "transaction_item_id": "00000000-0000-0000-0000-000000000005",
                "transaction_id": transaction_id,
                "product_id": product_id,
                "quantity": 1,
                "unit_price": Decimal("3.50"),
            }
        ],
    }


def test_load_all_inserts_tables_in_foreign_key_safe_order(monkeypatch):
    calls = []

    def fake_execute_values(cursor, sql, values, page_size):
        calls.append(
            {
                "sql": sql,
                "values": values,
                "page_size": page_size,
            }
        )

    monkeypatch.setattr(load.extras, "execute_values", fake_execute_values)
    connection = FakeConnection()

    counts = load.load_all(transformed_data(), connection, batch_size=50)

    assert counts == {
        "branches": 1,
        "payment_types": 1,
        "products": 1,
        "transactions": 1,
        "transaction_items": 1,
    }
    assert connection.committed is True
    assert connection.rolled_back is False
    assert [call["sql"].split()[2] for call in calls] == [
        "branches",
        "payment_type",
        "products",
        "transactions",
        "transaction_items",
    ]
    assert all(call["page_size"] == 50 for call in calls)


def test_load_all_rolls_back_if_insert_fails(monkeypatch):
    def fake_execute_values(cursor, sql, values, page_size):
        raise RuntimeError("database insert failed")

    monkeypatch.setattr(load.extras, "execute_values", fake_execute_values)
    connection = FakeConnection()

    try:
        load.load_all(transformed_data(), connection)
    except RuntimeError as error:
        assert "database insert failed" in str(error)
    else:
        raise AssertionError("Expected failed insert to be raised")

    assert connection.committed is False
    assert connection.rolled_back is True
