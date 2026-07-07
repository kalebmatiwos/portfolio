## SQL schema script

The database schema is stored as a standalone SQL file:

`databases/db-scripts/001_create_tables.sql`

This file creates the following tables:

- branches
- payment_type
- products
- transactions
- transaction_items

The schema uses UUID primary keys and foreign key relationships between the transaction, branch, payment method, product, and transaction item tables.

The previous Python-based schema creation script has been replaced so the schema can be used directly by the Docker PostgreSQL setup.