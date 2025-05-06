-- Drop existing tables 
DROP TABLE IF EXISTS movements;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS locations;

-- locations table 
CREATE TABLE locations (
    location_id TEXT PRIMARY KEY,
    city TEXT
);

-- products table 
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    description TEXT,
    condition TEXT,
    price REAL NOT NULL CHECK (price > 0 AND price <= 1000)
);

-- movements table 
CREATE TABLE movements (
    movement_id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    from_location TEXT,
    to_location TEXT,
    qty INTEGER NOT NULL CHECK (qty > 0),
    timestamp TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products (product_id),
    FOREIGN KEY (from_location) REFERENCES locations (location_id),
    FOREIGN KEY (to_location) REFERENCES locations (location_id),
    CHECK (from_location != to_location),
    CHECK (from_location IS NOT NULL OR to_location IS NOT NULL)
);

-- sample data for locations 
INSERT INTO locations (location_id, city) VALUES
    ('L001', 'Chennai'),
    ('L002', 'Bengaluru'),
    ('L003', 'Mumbai'),
    ('L004', 'Delhi');

-- sample data for products 
INSERT INTO products (product_id, name, type, description, condition, price) VALUES
    ('P001', 'Laptop', 'Electronics', '13-inch laptop with 8GB RAM', 'Refurbished', 450.00),
    ('P002', 'Sofa', 'Furniture', 'Three-seater leather sofa', 'Used', 300.00),
    ('P003', 'Jacket', 'Clothing', 'Winter jacket, size M', 'New', 80.00),
    ('P004', 'Headphones', 'Electronics', 'Wireless over-ear headphones', 'New', 120.00),
    ('P005', 'Dining Table', 'Furniture', 'Wooden table for 6 people', 'Used', 200.00);


INSERT INTO movements (movement_id, product_id, from_location, to_location, qty, timestamp) VALUES
    ('M001', 'P001', NULL, 'L001', 20, '2025-04-01 09:00:00'), 
    ('M002', 'P002', NULL, 'L001', 15, '2025-04-01 09:10:00'), 
    ('M003', 'P003', NULL, 'L002', 30, '2025-04-01 09:20:00'), 
    ('M004', 'P004', NULL, 'L003', 25, '2025-04-01 09:30:00'), 
    ('M005', 'P005', NULL, 'L003', 10, '2025-04-01 09:40:00'), 

    -- Subsequent movements
    ('M006', 'P001', 'L001', 'L002', 5, '2025-05-02 12:00:00'), 
    ('M007', 'P002', 'L001', 'L002', 5, '2025-05-02 12:10:00'), 
    ('M008', 'P003', 'L002', NULL, 3, '2025-05-03 14:00:00'),  
    ('M009', 'P004', 'L003', 'L001', 8, '2025-05-04 09:00:00'), 
    ('M010', 'P005', 'L003', 'L001', 2, '2025-05-05 11:00:00'); 