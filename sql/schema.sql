-- Trekking Management System : PostgreSQL Schema
-- Drops and recreates all tables, views, and indexes.

DROP VIEW IF EXISTS v_trek_reviews CASCADE;
DROP VIEW IF EXISTS v_rescue_dashboard CASCADE;
DROP VIEW IF EXISTS v_booking_details CASCADE;
DROP VIEW IF EXISTS v_trek_availability CASCADE;

DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS rescue_operations CASCADE;
DROP TABLE IF EXISTS shops CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS treks CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. USERS: Trekkers, Staff, and Admins
CREATE TABLE users (
    id                      SERIAL PRIMARY KEY,
    name                    VARCHAR(120) NOT NULL,
    username                VARCHAR(80)  NOT NULL UNIQUE,
    email                   VARCHAR(120) NOT NULL UNIQUE,
    contact                 VARCHAR(20),
    emergency_contact_name  VARCHAR(120),
    emergency_contact_phone VARCHAR(20),
    password_hash           VARCHAR(255) NOT NULL,
    role                    VARCHAR(10)  NOT NULL
                            CHECK (role IN ('admin', 'staff', 'user')),
    status                  VARCHAR(12)  NOT NULL DEFAULT 'approved'
                            CHECK (status IN ('approved', 'pending', 'blacklisted')),
    created_at              TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 2. TREKS: Expeditions catalog with itinerary, capacity, and pricing
CREATE TABLE treks (
    id                SERIAL PRIMARY KEY,
    name              VARCHAR(150) NOT NULL,
    destination       VARCHAR(150) NOT NULL,
    location          VARCHAR(150) NOT NULL,
    difficulty        VARCHAR(10)  NOT NULL
                      CHECK (difficulty IN ('Easy', 'Moderate', 'Hard')),
    duration          INTEGER      NOT NULL CHECK (duration > 0),
    base_cost         NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (base_cost >= 0),
    price             NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (price >= 0),
    max_capacity      INTEGER      NOT NULL CHECK (max_capacity > 0),
    total_slots       INTEGER      NOT NULL CHECK (total_slots > 0),
    assigned_staff_id INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    status            VARCHAR(10)  NOT NULL DEFAULT 'Open'
                      CHECK (status IN ('Open', 'Closed', 'Completed')),
    start_date        DATE,
    end_date          DATE,
    description       TEXT,
    itinerary         TEXT,
    image_url         VARCHAR(255),
    is_trending       BOOLEAN      DEFAULT FALSE,
    category          VARCHAR(50)  DEFAULT 'Trekking'
                      CHECK (category IN ('Adventure', 'Trekking', 'Camp Fire', 'Exploring')),
    created_at        TIMESTAMP    NOT NULL DEFAULT NOW(),
    CHECK (start_date IS NULL OR end_date IS NULL OR end_date >= start_date)
);

-- 3. BOOKINGS: Maps Trekkers to specific Treks with travel dates & party size
CREATE TABLE bookings (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER      NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    trek_id          INTEGER      NOT NULL REFERENCES treks(id) ON DELETE CASCADE,
    travel_date      DATE         NOT NULL DEFAULT CURRENT_DATE,
    num_participants INTEGER      NOT NULL DEFAULT 1 CHECK (num_participants > 0),
    total_price      NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (total_price >= 0),
    status           VARCHAR(15)  NOT NULL DEFAULT 'Confirmed'
                     CHECK (status IN ('Confirmed', 'Booked', 'Cancelled', 'Completed')),
    special_requests TEXT,
    booking_date     TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 4. TRANSACTIONS: Financial processing linked to Bookings
CREATE TABLE transactions (
    id             SERIAL PRIMARY KEY,
    booking_id     INTEGER      NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    transaction_id VARCHAR(100) NOT NULL UNIQUE,
    amount         NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    payment_method VARCHAR(50)  NOT NULL,
    status         VARCHAR(20)  NOT NULL DEFAULT 'Success'
                   CHECK (status IN ('Success', 'Pending', 'Refunded', 'Failed')),
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 5. SHOPS: Partner vendors catalog linked to specific Treks
CREATE TABLE shops (
    id             SERIAL PRIMARY KEY,
    name           VARCHAR(150) NOT NULL,
    category       VARCHAR(50)  NOT NULL
                   CHECK (category IN ('Gear Rental', 'Souvenir', 'Photography', 'Food & Cafe', 'Medical & Essentials')),
    coordinates    VARCHAR(100) NOT NULL,
    contact_number VARCHAR(30),
    rating         NUMERIC(2,1) DEFAULT 4.8,
    description    TEXT,
    image_url      VARCHAR(255),
    trek_id        INTEGER      NOT NULL REFERENCES treks(id) ON DELETE CASCADE,
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 6. RESCUE_OPERATIONS: Emergency logistics and dispatches
CREATE TABLE rescue_operations (
    id               SERIAL PRIMARY KEY,
    trekker_id       INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    staff_id         INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    trek_id          INTEGER      REFERENCES treks(id) ON DELETE SET NULL,
    emergency_type   VARCHAR(100) NOT NULL,
    last_coordinates VARCHAR(100) NOT NULL,
    alert_time       TIMESTAMP    NOT NULL DEFAULT NOW(),
    status           VARCHAR(30)  NOT NULL DEFAULT 'Active'
                     CHECK (status IN ('Active', 'Dispatched', 'In Progress', 'Evacuated', 'Resolved')),
    notes            TEXT,
    updated_at       TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 7. REVIEWS: Customer reviews & 1-5 star ratings for treks
CREATE TABLE reviews (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trek_id     INTEGER   NOT NULL REFERENCES treks(id) ON DELETE CASCADE,
    rating      INTEGER   NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment     TEXT      NOT NULL,
    is_featured BOOLEAN   DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- INDEXES
CREATE INDEX idx_bookings_trek   ON bookings (trek_id);
CREATE INDEX idx_bookings_user   ON bookings (user_id);
CREATE INDEX idx_treks_staff     ON treks (assigned_staff_id);
CREATE INDEX idx_treks_trending  ON treks (is_trending);
CREATE INDEX idx_treks_category  ON treks (category);
CREATE INDEX idx_shops_trek      ON shops (trek_id);
CREATE INDEX idx_rescue_trekker  ON rescue_operations (trekker_id);
CREATE INDEX idx_rescue_staff    ON rescue_operations (staff_id);
CREATE INDEX idx_reviews_trek    ON reviews (trek_id);

-- VIEWS

-- Live trek availability view including booked participants and ratings
CREATE VIEW v_trek_availability AS
SELECT t.id,
       t.name,
       t.destination,
       t.location,
       t.difficulty,
       t.duration,
       t.base_cost,
       t.price,
       t.max_capacity,
       t.total_slots,
       t.assigned_staff_id,
       t.status,
       t.start_date,
       t.end_date,
       t.description,
       t.itinerary,
       t.image_url,
       t.is_trending,
       t.category,
       t.created_at,
       u.name AS staff_name,
       u.contact AS staff_contact,
       COALESCE(SUM(b.num_participants) FILTER (WHERE b.status IN ('Confirmed', 'Booked', 'Completed')), 0) AS booked_count,
       t.total_slots - COALESCE(SUM(b.num_participants) FILTER (WHERE b.status IN ('Confirmed', 'Booked', 'Completed')), 0) AS available_slots,
       COALESCE(ROUND(AVG(r.rating), 1), 5.0) AS avg_rating,
       COUNT(DISTINCT r.id) AS review_count
FROM treks t
LEFT JOIN users u    ON u.id = t.assigned_staff_id
LEFT JOIN bookings b ON b.trek_id = t.id
LEFT JOIN reviews r  ON r.trek_id = t.id
GROUP BY t.id, u.name, u.contact;

-- Comprehensive booking view with trekker, trek, and transaction details
CREATE VIEW v_booking_details AS
SELECT b.id,
       b.booking_date,
       b.travel_date,
       b.num_participants,
       b.total_price,
       b.status,
       b.special_requests,
       b.user_id,
       u.name AS user_name,
       u.email AS user_email,
       u.contact AS user_contact,
       u.emergency_contact_name,
       u.emergency_contact_phone,
       b.trek_id,
       t.name AS trek_name,
       t.destination,
       t.location AS trek_location,
       t.difficulty,
       t.duration,
       t.image_url AS trek_image,
       t.assigned_staff_id,
       s.name AS staff_name,
       tx.id AS transaction_db_id,
       tx.transaction_id,
       tx.amount AS transaction_amount,
       tx.payment_method,
       tx.status AS payment_status
FROM bookings b
JOIN users u         ON u.id = b.user_id
JOIN treks t         ON t.id = b.trek_id
LEFT JOIN users s    ON s.id = t.assigned_staff_id
LEFT JOIN transactions tx ON tx.booking_id = b.id;

-- Rescue operations monitoring dashboard view
CREATE VIEW v_rescue_dashboard AS
SELECT ro.id,
       ro.emergency_type,
       ro.last_coordinates,
       ro.alert_time,
       ro.status,
       ro.notes,
       ro.updated_at,
       ro.trekker_id,
       u.name AS trekker_name,
       u.contact AS trekker_contact,
       u.emergency_contact_name,
       u.emergency_contact_phone,
       ro.staff_id,
       s.name AS staff_name,
       s.contact AS staff_contact,
       ro.trek_id,
       t.name AS trek_name,
       t.location AS trek_location
FROM rescue_operations ro
JOIN users u         ON u.id = ro.trekker_id
LEFT JOIN users s    ON s.id = ro.staff_id
LEFT JOIN treks t    ON t.id = ro.trek_id;

-- Reviews view with user and trek context
CREATE VIEW v_trek_reviews AS
SELECT r.id,
       r.rating,
       r.comment,
       r.is_featured,
       r.created_at,
       r.user_id,
       u.name AS user_name,
       u.role AS user_role,
       r.trek_id,
       t.name AS trek_name,
       t.destination AS trek_destination
FROM reviews r
JOIN users u ON u.id = r.user_id
JOIN treks t ON t.id = r.trek_id;
