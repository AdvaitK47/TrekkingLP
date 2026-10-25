-- Comprehensive SQL Queries for Trekking Management System (PostgreSQL)
-- Covers 7 Tables: users, treks, bookings, transactions, shops, rescue_operations, reviews

-- 1. SELECT with WHERE & ORDER BY: Trending treks with available capacity
SELECT id, name, destination, difficulty, base_cost, available_slots, avg_rating
FROM v_trek_availability
WHERE is_trending = TRUE AND available_slots > 0
ORDER BY base_cost ASC;

-- 2. Financial Aggregation: Total platform revenue, average booking value, successful transactions
SELECT COUNT(tx.id) AS total_transactions,
       SUM(tx.amount) AS total_revenue,
       ROUND(AVG(tx.amount), 2) AS avg_transaction_value,
       MIN(tx.amount) AS min_transaction,
       MAX(tx.amount) AS max_transaction
FROM transactions tx
WHERE tx.status = 'Success';

-- 3. Multi-table JOIN (4 tables): Booking financial audit trail
SELECT b.id AS booking_id,
       u.name AS trekker_name,
       u.email AS trekker_email,
       t.name AS trek_name,
       b.travel_date,
       b.num_participants,
       b.total_price,
       tx.transaction_id,
       tx.payment_method,
       tx.status AS payment_status
FROM bookings b
JOIN users u ON u.id = b.user_id
JOIN treks t ON t.id = b.trek_id
LEFT JOIN transactions tx ON tx.booking_id = b.id
ORDER BY b.booking_date DESC;

-- 4. GROUP BY + HAVING: High-revenue treks with at least 2 bookings
SELECT t.name AS trek_name,
       t.destination,
       COUNT(b.id) AS confirmed_bookings,
       SUM(b.num_participants) AS total_trekkers,
       SUM(tx.amount) AS total_revenue
FROM treks t
JOIN bookings b ON b.trek_id = t.id
JOIN transactions tx ON tx.booking_id = b.id
WHERE b.status IN ('Confirmed', 'Completed') AND tx.status = 'Success'
GROUP BY t.id, t.name, t.destination
HAVING COUNT(b.id) >= 2
ORDER BY total_revenue DESC;

-- 5. Emergency Logistics Query: Active rescue operations with staff dispatches
SELECT ro.id AS alert_id,
       u.name AS distressed_trekker,
       u.contact AS trekker_phone,
       u.emergency_contact_name,
       u.emergency_contact_phone,
       ro.emergency_type,
       ro.last_coordinates,
       s.name AS assigned_staff,
       s.contact AS staff_phone,
       ro.status AS rescue_status,
       ro.alert_time
FROM rescue_operations ro
JOIN users u ON u.id = ro.trekker_id
LEFT JOIN users s ON s.id = ro.staff_id
WHERE ro.status IN ('Active', 'Dispatched', 'In Progress')
ORDER BY ro.alert_time DESC;

-- 6. Vendor Ecosystem Query: Partner shops categorized per trek with ratings
SELECT t.name AS trek_name,
       s.name AS shop_name,
       s.category,
       s.coordinates,
       s.contact_number,
       s.rating
FROM shops s
JOIN treks t ON t.id = s.trek_id
ORDER BY t.name, s.rating DESC;

-- 7. Reviews & Customer Satisfaction: Average rating and review count per expedition
SELECT t.name AS trek_name,
       t.destination,
       t.difficulty,
       ROUND(AVG(r.rating), 2) AS avg_rating,
       COUNT(r.id) AS total_reviews
FROM treks t
LEFT JOIN reviews r ON r.trek_id = t.id
GROUP BY t.id, t.name, t.destination, t.difficulty
ORDER BY avg_rating DESC NULLS LAST;

-- 8. Subquery with NOT EXISTS: Registered trekkers without any rescue incidents
SELECT u.id, u.name, u.email, u.contact
FROM users u
WHERE u.role = 'user'
  AND NOT EXISTS (
      SELECT 1 FROM rescue_operations ro WHERE ro.trekker_id = u.id
  );

-- 9. Correlated Subquery: Treks priced above the average trek price
SELECT name, destination, base_cost
FROM treks
WHERE base_cost > (SELECT AVG(base_cost) FROM treks WHERE status = 'Open')
ORDER BY base_cost DESC;

-- 10. Staff Workload & Safety Assignments
SELECT s.name AS staff_name,
       s.contact,
       COUNT(DISTINCT t.id) AS active_treks_led,
       COUNT(DISTINCT ro.id) AS rescues_handled
FROM users s
LEFT JOIN treks t ON t.assigned_staff_id = s.id AND t.status = 'Open'
LEFT JOIN rescue_operations ro ON ro.staff_id = s.id
WHERE s.role = 'staff' AND s.status = 'approved'
GROUP BY s.id, s.name, s.contact
ORDER BY active_treks_led DESC;
