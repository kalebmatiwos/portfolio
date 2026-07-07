import psycopg2.extras as extras


def _insert_rows(cursor, table, columns, records, batch_size=100):
    if not records:
        return 0

    values = [tuple(record[col] for col in columns) for record in records]
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s"
    extras.execute_values(cursor, sql, values, page_size=batch_size)
    return len(values)


def load_branches(branches, cursor, batch_size=100):
    return _insert_rows(
        cursor,
        "branches",
        ["branch_id", "branch_name"],
        branches,
        batch_size,
    )


def load_payment_types(payment_types, cursor, batch_size=100):
    return _insert_rows(
        cursor,
        "payment_type",
        ["payment_method_id", "payment_method"],
        payment_types,
        batch_size,
    )


def load_products(products, cursor, batch_size=100):
    return _insert_rows(
        cursor,
        "products",
        ["product_id", "product_name", "current_price"],
        products,
        batch_size,
    )


def load_transactions(transactions, cursor, batch_size=100):
    return _insert_rows(
        cursor,
        "transactions",
        [
            "transaction_id",
            "branch_id",
            "payment_method_id",
            "transaction_timestamp",
            "transaction_total",
        ],
        transactions,
        batch_size,
    )


def load_transaction_items(transaction_items, cursor, batch_size=100):
    return _insert_rows(
        cursor,
        "transaction_items",
        [
            "transaction_item_id",
            "transaction_id",
            "product_id",
            "quantity",
            "unit_price",
        ],
        transaction_items,
        batch_size,
    )


def load_all(transformed_data, conn, batch_size=100):
    counts = {
        "branches": 0,
        "payment_types": 0,
        "products": 0,
        "transactions": 0,
        "transaction_items": 0,
    }

    try:
        with conn.cursor() as cursor:
            counts["branches"] = load_branches(
                transformed_data.get("branches", []), cursor, batch_size
            )
            counts["payment_types"] = load_payment_types(
                transformed_data.get("payment_types", []), cursor, batch_size
            )
            counts["products"] = load_products(
                transformed_data.get("products", []), cursor, batch_size
            )
            counts["transactions"] = load_transactions(
                transformed_data.get("transactions", []), cursor, batch_size
            )
            counts["transaction_items"] = load_transaction_items(
                transformed_data.get("transaction_items", []), cursor, batch_size
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return counts
