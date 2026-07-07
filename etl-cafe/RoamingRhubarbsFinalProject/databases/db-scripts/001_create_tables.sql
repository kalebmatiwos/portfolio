-- ============================================
-- BRANCHES
-- ============================================

CREATE TABLE IF NOT EXISTS branches (
    branch_id VARCHAR(36) PRIMARY KEY,
    branch_name VARCHAR(255) NOT NULL
);

-- ============================================
-- PAYMENT TYPES
-- ============================================

CREATE TABLE IF NOT EXISTS payment_type (
    payment_method_id VARCHAR(36) PRIMARY KEY,
    payment_method VARCHAR(100) NOT NULL
);

-- ============================================
-- PRODUCTS
-- ============================================

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(36) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    current_price DECIMAL(10,2) NOT NULL
);

-- ============================================
-- TRANSACTIONS
-- ============================================

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(36) PRIMARY KEY,

    branch_id VARCHAR(36) NOT NULL,
    payment_method_id VARCHAR(36) NOT NULL,

    transaction_timestamp TIMESTAMP NOT NULL,
    transaction_total DECIMAL(10,2) NOT NULL,

    CONSTRAINT fk_transactions_branch
        FOREIGN KEY (branch_id)
        REFERENCES branches(branch_id),

    CONSTRAINT fk_transactions_payment
        FOREIGN KEY (payment_method_id)
        REFERENCES payment_type(payment_method_id)
);

-- ============================================
-- TRANSACTION ITEMS
-- ============================================

CREATE TABLE IF NOT EXISTS transaction_items (
    transaction_item_id VARCHAR(36) PRIMARY KEY,

    transaction_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,

    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,

    CONSTRAINT fk_transaction_items_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id),

    CONSTRAINT fk_transaction_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);