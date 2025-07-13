# SQL Code Examples for Model Testing

## 🎯 **Excellent Quality SQL (Score: 8-10)**

### **Correctness - Excellent**
```sql
-- Well-structured query with proper joins and conditions
SELECT 
    u.user_id,
    u.username,
    u.email,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE u.is_active = true 
    AND u.created_date >= '2024-01-01'
    AND o.order_status IN ('completed', 'shipped')
GROUP BY u.user_id, u.username, u.email
HAVING COUNT(o.order_id) > 0
ORDER BY total_spent DESC;
```

### **Efficiency - Excellent**
```sql
-- Optimized query with proper indexing hints and efficient joins
SELECT /*+ INDEX(users idx_users_email) */
    u.user_id,
    u.email,
    p.product_name,
    p.price
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
WHERE u.email LIKE '%@gmail.com'
    AND o.order_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    AND p.category_id = 5;
```

### **Readability - Excellent**
```sql
-- Well-formatted and documented query
/*
 * Get monthly sales report for active customers
 * Filters: Active users, completed orders, last 12 months
 * Returns: Customer info, order count, total spent
 */
SELECT 
    -- Customer information
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    
    -- Order statistics
    COUNT(DISTINCT o.order_id) as order_count,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as avg_order_value,
    
    -- Date formatting
    DATE_FORMAT(o.order_date, '%Y-%m') as order_month
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id
WHERE u.is_active = true
    AND o.order_status = 'completed'
    AND o.order_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
GROUP BY 
    u.user_id, 
    u.first_name, 
    u.last_name, 
    u.email,
    DATE_FORMAT(o.order_date, '%Y-%m')
ORDER BY 
    order_month DESC, 
    total_spent DESC;
```

### **Security - Excellent**
```sql
-- Secure query with proper parameterization and validation
SELECT 
    u.user_id,
    u.username,
    u.email
FROM users u
WHERE u.user_id = ?  -- Parameterized to prevent SQL injection
    AND u.is_active = true
    AND u.account_type IN ('premium', 'standard')
    AND u.created_date >= '2020-01-01'
LIMIT 100;  -- Prevent excessive data retrieval
```

### **Scalability - Excellent**
```sql
-- Scalable query with proper partitioning and indexing
SELECT 
    p.product_id,
    p.product_name,
    p.category_id,
    COUNT(oi.order_item_id) as times_ordered,
    SUM(oi.quantity) as total_quantity_sold
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
    AND oi.created_date >= DATE_SUB(NOW(), INTERVAL 90 DAY)
WHERE p.is_active = true
    AND p.category_id IN (1, 2, 3, 4, 5)
GROUP BY p.product_id, p.product_name, p.category_id
HAVING COUNT(oi.order_item_id) > 0
ORDER BY total_quantity_sold DESC
LIMIT 50;
```

---

## 🟡 **Good Quality SQL (Score: 6-7)**

### **Correctness - Good**
```sql
-- Generally correct but could be improved
SELECT user_id, username, email, order_count
FROM users u, orders o
WHERE u.user_id = o.user_id
AND u.active = 1
GROUP BY user_id;
```

### **Efficiency - Good**
```sql
-- Reasonable but not optimized
SELECT u.name, o.total
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.date > '2024-01-01'
ORDER BY o.total DESC;
```

### **Readability - Good**
```sql
-- Readable but could use better formatting
SELECT 
    u.user_id,
    u.name,
    COUNT(o.order_id) as orders
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE u.active = true
GROUP BY u.user_id, u.name
HAVING orders > 0;
```

### **Security - Good**
```sql
-- Basic security but could be improved
SELECT user_id, username, email
FROM users
WHERE user_id = 123
AND active = 1;
```

### **Scalability - Good**
```sql
-- Works but could be more scalable
SELECT product_id, name, price
FROM products
WHERE category = 'electronics'
ORDER BY price DESC;
```

---

## 🔴 **Poor Quality SQL (Score: 1-5)**

### **Correctness - Poor**
```sql
-- Multiple issues: missing GROUP BY, ambiguous columns
SELECT user_id, name, COUNT(*)
FROM users, orders
WHERE user_id = user_id  -- Ambiguous column reference
AND active = 1;
```

### **Efficiency - Poor**
```sql
-- Very inefficient with SELECT * and no indexes
SELECT *
FROM users u, orders o, products p, categories c
WHERE u.id = o.user_id
AND o.product_id = p.id
AND p.category_id = c.id
AND u.name LIKE '%john%';
```

### **Readability - Poor**
```sql
-- Poorly formatted and hard to read
SELECT u.id,u.name,u.email,o.total FROM users u,orders o WHERE u.id=o.user_id AND u.active=1 AND o.total>100 ORDER BY o.total DESC;
```

### **Security - Poor (VULNERABLE TO SQL INJECTION)**
```sql
-- DANGEROUS: Vulnerable to SQL injection
SELECT user_id, username, password
FROM users
WHERE username = 'admin' OR 1=1;  -- This would return all users!
```

### **Scalability - Poor**
```sql
-- Will cause performance issues with large datasets
SELECT *
FROM users
WHERE email LIKE '%@gmail.com'
ORDER BY created_date;  -- No limit, could return millions of rows
```

---

## 🚨 **Very Poor Quality SQL (Score: 1-2)**

### **Correctness - Very Poor**
```sql
-- Completely broken query
SELECT user_id, name
FROM users
WHERE user_id = user_id  -- Always true, returns all users
GROUP BY name;  -- Missing user_id in GROUP BY
```

### **Efficiency - Very Poor**
```sql
-- Extremely inefficient with multiple subqueries
SELECT u.name, 
    (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count,
    (SELECT SUM(total) FROM orders WHERE user_id = u.id) as total_spent,
    (SELECT AVG(total) FROM orders WHERE user_id = u.id) as avg_order
FROM users u
WHERE u.active = 1;
```

### **Readability - Very Poor**
```sql
-- Completely unreadable
SELECT u.id,u.n,u.e,o.t FROM u,o WHERE u.id=o.uid AND u.a=1 AND o.t>50 ORDER BY o.t;
```

### **Security - Very Poor (CRITICAL VULNERABILITY)**
```sql
-- CRITICAL: Drop table vulnerability
SELECT * FROM users WHERE username = 'admin'; DROP TABLE users; --';
```

### **Scalability - Very Poor**
```sql
-- Will crash the database
SELECT *
FROM users u
CROSS JOIN orders o
CROSS JOIN products p
WHERE u.active = 1;  -- Cartesian product!
```

---

## 🧪 **Test Cases for Specific Metrics**

### **Testing Error Handling**
```sql
-- Should handle gracefully
SELECT user_id, name, 
    CASE 
        WHEN total_spent > 1000 THEN 'Premium'
        WHEN total_spent > 500 THEN 'Standard'
        ELSE 'Basic'
    END as customer_type
FROM users
WHERE active = 1;
```

### **Testing Best Practices**
```sql
-- Good practices: aliases, explicit joins, meaningful names
SELECT 
    u.user_id,
    u.first_name,
    u.last_name,
    COUNT(o.order_id) as total_orders,
    COALESCE(SUM(o.total_amount), 0) as total_spent
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id 
    AND o.order_status = 'completed'
WHERE u.is_active = true
    AND u.created_date >= '2020-01-01'
GROUP BY u.user_id, u.first_name, u.last_name
HAVING COUNT(o.order_id) > 0
ORDER BY total_spent DESC;
```

### **Testing Documentation**
```sql
-- Well-documented query
/*
 * Customer Lifetime Value Analysis
 * 
 * Purpose: Calculate CLV for active customers
 * Filters: Active users, completed orders only
 * Output: Customer ID, name, order count, total spent, CLV
 * 
 * Author: Data Team
 * Last Updated: 2024-01-15
 */
SELECT 
    u.user_id,
    CONCAT(u.first_name, ' ', u.last_name) as full_name,
    COUNT(o.order_id) as order_count,
    SUM(o.total_amount) as total_spent,
    SUM(o.total_amount) / COUNT(o.order_id) as avg_order_value
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id
WHERE u.is_active = true
    AND o.order_status = 'completed'
GROUP BY u.user_id, u.first_name, u.last_name
ORDER BY total_spent DESC;
```

---

## 📊 **Quick Test Suite**

### **Copy these examples to test different aspects:**

**For Excellent Quality Testing:**
```sql
SELECT 
    u.user_id,
    u.username,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE u.is_active = true 
    AND o.order_status IN ('completed', 'shipped')
GROUP BY u.user_id, u.username
HAVING COUNT(o.order_id) > 0
ORDER BY total_spent DESC;
```

**For Poor Quality Testing:**
```sql
SELECT u.id,u.name,o.total FROM users u,orders o WHERE u.id=o.user_id AND u.active=1 ORDER BY o.total;
```

**For Security Testing:**
```sql
SELECT user_id, username, email FROM users WHERE username = 'admin' OR 1=1;
```

Use these examples to test how well your model evaluates different aspects of SQL code quality! 🚀 