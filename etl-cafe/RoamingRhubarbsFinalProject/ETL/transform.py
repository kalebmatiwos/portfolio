from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import uuid


def generate_uuid():
    return str(uuid.uuid4())
# Generate UUID as strings
#Database schema uses UUID as primary keys, so IDs get created in python.

def format_money(value):
    return Decimal(str(value).strip()).quantize(Decimal("0.01"))
#Price values get converted into a decimal with two decimal places.

def format_timestamp(timestamp_value):
    return datetime.strptime(timestamp_value.strip(), "%d/%m/%Y %H:%M")
#This function converts timestamp from CSV into Python object

def remove_sensitive_data(raw_rows):
    cleaned_rows = []

    for row in raw_rows:
        cleaned_row = {
            "timestamp": row["timestamp"],
            "location": row["location"],
            "items ordered": row["items ordered"],
            "total amount": row["total amount"],
            "payment method": row["payment method"],
        }

        cleaned_rows.append(cleaned_row)

    return cleaned_rows
#This function removes customer's sensitive data

def parse_items_ordered(items_ordered):
    item_quantities = defaultdict(int)

    raw_items = items_ordered.split(",")

    for raw_item in raw_items:
        raw_item = raw_item.strip()

        if not raw_item:
            continue

        product_name, unit_price = raw_item.rsplit(" - ", 1)

        product_name = product_name.strip()
        unit_price = format_money(unit_price)

        item_key = (product_name, unit_price)
        item_quantities[item_key] += 1

    parsed_items = []

    for item_key, quantity in item_quantities.items():
        product_name, unit_price = item_key

        parsed_items.append(
            {
                "product_name": product_name,
                "quantity": quantity,
                "unit_price": unit_price,
            }
        )

    return parsed_items
#This converts 'items ordered' field into separate product records
#It splits each item using only the final '-'.

def normalise_data(cleaned_rows):
    branches = []
    payment_types = []
    products = []
    transactions = []
    transaction_items = []

    branch_lookup = {}
    payment_type_lookup = {}
    product_lookup = {}

    for row in cleaned_rows:
        location = row["location"].strip()
        payment_method = row["payment method"].strip()

        if location not in branch_lookup:
            branch_id = generate_uuid()
            branch_lookup[location] = branch_id

            branches.append(
                {
                    "branch_id": branch_id,
                    "branch_name": location,
                }
            )

        if payment_method not in payment_type_lookup:
            payment_method_id = generate_uuid()
            payment_type_lookup[payment_method] = payment_method_id

            payment_types.append(
                {
                    "payment_method_id": payment_method_id,
                    "payment_method": payment_method,
                }
            )

        transaction_id = generate_uuid()

        transactions.append(
            {
                "transaction_id": transaction_id,
                "branch_id": branch_lookup[location],
                "payment_method_id": payment_type_lookup[payment_method],
                "transaction_timestamp": format_timestamp(row["timestamp"]),
                "transaction_total": format_money(row["total amount"]),
            }
        )

        parsed_items = parse_items_ordered(row["items ordered"])

        for item in parsed_items:
            product_key = (
                item["product_name"],
                item["unit_price"],
            )

            if product_key not in product_lookup:
                product_id = generate_uuid()
                product_lookup[product_key] = product_id

                products.append(
                    {
                        "product_id": product_id,
                        "product_name": item["product_name"],
                        "current_price": item["unit_price"],
                    }
                )

            transaction_items.append(
                {
                    "transaction_item_id": generate_uuid(),
                    "transaction_id": transaction_id,
                    "product_id": product_lookup[product_key],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                }
            )

    return {
        "branches": branches,
        "payment_types": payment_types,
        "products": products,
        "transactions": transactions,
        "transaction_items": transaction_items,
    }
#This converts previously cleaned CSV rows into records that match the database schema

def etl_transform(rawdata):
    cleaned_data = remove_sensitive_data(rawdata)
    transformed_data = normalise_data(cleaned_data)

    print("Transform completed successfully.")
    print(f"Branches created: {len(transformed_data['branches'])}")
    print(f"Payment types created: {len(transformed_data['payment_types'])}")
    print(f"Products created: {len(transformed_data['products'])}")
    print(f"Transactions created: {len(transformed_data['transactions'])}")
    print(f"Transaction items created: {len(transformed_data['transaction_items'])}")

    return transformed_data
#This function runs the transformation stage of the ETL pipeline.
#It removes sensitive data, normalizes the remaining data, returns the transformed data
#It also communicates to the user what has been done and in what amount.