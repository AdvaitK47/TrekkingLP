import os
import re
import sqlite3
from flask import g
import psycopg2
import psycopg2.extras
from config import DB_CONFIG, DB_NAME

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "trekking_fallback.db")

_DB_ENGINE = None  # 'postgres' or 'sqlite'


def detect_engine():
    global _DB_ENGINE
    if _DB_ENGINE is not None:
        return _DB_ENGINE
    try:
        conn = psycopg2.connect(dbname=DB_NAME, **DB_CONFIG, connect_timeout=2)
        conn.close()
        _DB_ENGINE = "postgres"
        print(f"[DB] Connected to PostgreSQL database '{DB_NAME}'.")
    except Exception as e:
        _DB_ENGINE = "sqlite"
        print(f"[DB] PostgreSQL not reachable ({e}). Using local fallback engine (SQLite).")
        init_sqlite_fallback()
    return _DB_ENGINE


def init_sqlite_fallback():
    # Initializes sqlite database with identical tables, views, and seed data if not initialized
    need_seed = not os.path.exists(SQLITE_DB_PATH)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        contact TEXT,
        emergency_contact_name TEXT,
        emergency_contact_phone TEXT,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin', 'staff', 'user')),
        status TEXT NOT NULL DEFAULT 'approved' CHECK (status IN ('approved', 'pending', 'blacklisted')),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS treks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        destination TEXT NOT NULL,
        location TEXT NOT NULL,
        difficulty TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Moderate', 'Hard')),
        duration INTEGER NOT NULL CHECK (duration > 0),
        base_cost NUMERIC(10,2) NOT NULL DEFAULT 0,
        price NUMERIC(10,2) NOT NULL DEFAULT 0,
        max_capacity INTEGER NOT NULL CHECK (max_capacity > 0),
        total_slots INTEGER NOT NULL CHECK (total_slots > 0),
        assigned_staff_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        status TEXT NOT NULL DEFAULT 'Open' CHECK (status IN ('Open', 'Closed', 'Completed')),
        start_date DATE,
        end_date DATE,
        description TEXT,
        itinerary TEXT,
        image_url TEXT,
        is_trending BOOLEAN DEFAULT 0,
        category TEXT DEFAULT 'Trekking' CHECK (category IN ('Adventure', 'Trekking', 'Camp Fire', 'Exploring')),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        trek_id INTEGER NOT NULL REFERENCES treks(id) ON DELETE CASCADE,
        travel_date DATE NOT NULL DEFAULT (CURRENT_DATE),
        num_participants INTEGER NOT NULL DEFAULT 1,
        total_price NUMERIC(10,2) NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Confirmed' CHECK (status IN ('Confirmed', 'Booked', 'Cancelled', 'Completed')),
        special_requests TEXT,
        booking_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
        transaction_id TEXT NOT NULL UNIQUE,
        amount NUMERIC(10,2) NOT NULL,
        payment_method TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Success' CHECK (status IN ('Success', 'Pending', 'Refunded', 'Failed')),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS shops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL CHECK (category IN ('Gear Rental', 'Souvenir', 'Photography', 'Food & Cafe', 'Medical & Essentials')),
        coordinates TEXT NOT NULL,
        contact_number TEXT,
        rating NUMERIC(2,1) DEFAULT 4.8,
        description TEXT,
        image_url TEXT,
        trek_id INTEGER NOT NULL REFERENCES treks(id) ON DELETE CASCADE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS rescue_operations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trekker_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        staff_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        trek_id INTEGER REFERENCES treks(id) ON DELETE SET NULL,
        emergency_type TEXT NOT NULL,
        last_coordinates TEXT NOT NULL,
        alert_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Dispatched', 'In Progress', 'Evacuated', 'Resolved')),
        notes TEXT,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        trek_id INTEGER NOT NULL REFERENCES treks(id) ON DELETE CASCADE,
        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
        comment TEXT NOT NULL,
        is_featured BOOLEAN DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    DROP VIEW IF EXISTS v_trek_availability;
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
           COALESCE((SELECT SUM(b.num_participants) FROM bookings b WHERE b.trek_id = t.id AND b.status IN ('Confirmed', 'Booked', 'Completed')), 0) AS booked_count,
           t.total_slots - COALESCE((SELECT SUM(b.num_participants) FROM bookings b WHERE b.trek_id = t.id AND b.status IN ('Confirmed', 'Booked', 'Completed')), 0) AS available_slots,
           COALESCE((SELECT ROUND(AVG(r.rating), 1) FROM reviews r WHERE r.trek_id = t.id), 5.0) AS avg_rating,
           (SELECT COUNT(r.id) FROM reviews r WHERE r.trek_id = t.id) AS review_count
    FROM treks t
    LEFT JOIN users u ON u.id = t.assigned_staff_id;

    DROP VIEW IF EXISTS v_booking_details;
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
    JOIN users u ON u.id = b.user_id
    JOIN treks t ON t.id = b.trek_id
    LEFT JOIN users s ON s.id = t.assigned_staff_id
    LEFT JOIN transactions tx ON tx.booking_id = b.id;

    DROP VIEW IF EXISTS v_rescue_dashboard;
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
    JOIN users u ON u.id = ro.trekker_id
    LEFT JOIN users s ON s.id = ro.staff_id
    LEFT JOIN treks t ON t.id = ro.trek_id;

    DROP VIEW IF EXISTS v_trek_reviews;
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
    """)

    # Seed data if empty
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        seed_sqlite(conn)

    conn.commit()
    conn.close()


def seed_sqlite(conn):
    cur = conn.cursor()
    # Users
    users_data = [
        (1, 'Alexander Vance',  'admin',  'admin@mountains.expedition', '+1-555-0199', 'Sarah Vance',     '+1-555-0198', 'pbkdf2:sha256:1000000$aeWGCxYs1exlBdzZ$808c7a1047bd1d52784959225400bac0c2c73bc0c9f8389f0fc9bf2d3360d0c9', 'admin', 'approved'),
        (2, 'Tenzing Norgay',   'tenzing', 'tenzing@mountains.expedition', '+977-98110011', 'Pasang Lhamu',  '+977-98110012', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'staff', 'approved'),
        (3, 'Elena Rostova',    'elena',   'elena@mountains.expedition',   '+41-79-555123',  'Dmitri Rostov', '+41-79-555124', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'staff', 'approved'),
        (4, 'Ravi Sharma',      'ravi',    'ravi@mountains.expedition',    '+91-9822334455', 'Pooja Sharma',  '+91-9822334456', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'staff', 'approved'),
        (5, 'Marco Rossi',      'marco',   'marco@mountains.expedition',   '+39-333-123456', 'Sofia Rossi',   '+39-333-123457', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'staff', 'pending'),
        (6, 'Liam Hemsworth',   'liam',    'liam.h@adventurer.io',         '+1-415-8901234', 'Karen Hemsworth','+1-415-8901235', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
        (7, 'Aria Stark',       'aria',    'aria.stark@winterfell.org',    '+44-7700-90012', 'Ned Stark',     '+44-7700-90013', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
        (8, 'David Miller',     'david',   'david.miller@globaltrek.com',  '+1-212-7894561', 'Lisa Miller',   '+1-212-7894562', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
        (9, 'Chloe Bennett',    'chloe',   'chloe.b@wanderlust.net',       '+61-491-570156', 'James Bennett', '+61-491-570157', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
        (10, 'Aarav Patel',     'aarav',   'aarav.patel@himalayas.in',     '+91-9988776655', 'Sunita Patel',  '+91-9988776656', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
        (11, 'Maya Lin',        'maya',    'maya.lin@summitclub.com',      '+1-604-5550188', 'Wei Lin',       '+1-604-5550189', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
        (12, 'Julian Fischer',  'julian',  'julian.f@alpinist.de',         '+49-170-1234567','Ursula Fischer', '+49-170-1234568','pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'blacklisted'),
    ]
    cur.executemany("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)", users_data)

    # Treks
    treks_data = [
        (1, 'Iceland Hiking Trips', 'Iceland Fjords & Highlands', 'Iceland', 'Hard', 7, 1850.00, 1850.00, 16, 16, 3, 'Open', '2026-11-20', '2026-11-27',
         'Conquer the dramatic volcanic ridges and glacial valleys of southern Iceland. An adrenaline-filled trek crossing lava fields and geothermal springs.',
         'Day 1: Reykjavik Basecamp briefing & gear check. Day 2: Landmannalaugar geothermal fields. Day 3: Hrafntinnusker high pass snow crossing. Day 4: Lake Alftavatn glacial crossing. Day 5: Emstrur volcanic canyons. Day 6: Thorsmork birch valley summit. Day 7: Skogar waterfalls & hot springs celebration.',
         'static/images/iceland_hiking.jpg', 1, 'Adventure'),

        (2, 'Everest High Pass Expedition', 'Khumbu Valley', 'Nepal', 'Hard', 12, 2400.00, 2400.00, 12, 12, 2, 'Open', '2026-11-15', '2026-11-27',
         'Ascend into the roof of the world through rhododendron forests, suspension bridges, and dramatic high altitude Himalayan glacial moraines.',
         'Day 1-2: Flight to Lukla & trek to Namche Bazaar. Day 3: Acclimatization hike to Everest View Hotel. Day 4: Tengboche monastery blessing. Day 5: Dingboche alpine plateau. Day 6: Lobuche glacier edge. Day 7: Everest Base Camp & Kala Patthar 5,545m sunrise. Day 8-12: Descent via Pangboche & return flight.',
         'static/images/6.jpg', 1, 'Trekking'),

        (3, 'Patagonia Glacial Traverse', 'Perito Moreno & Fitz Roy', 'Patagonia, Argentina', 'Moderate', 6, 1650.00, 1650.00, 14, 14, 3, 'Open', '2026-12-05', '2026-12-11',
         'Witness gargantuan turquoise icebergs, sheer granite towers, and untouched glacial lakes on this once-in-a-lifetime South American pilgrimage.',
         'Day 1: El Calafate welcome dinner. Day 2: Perito Moreno ice walk with crampons. Day 3: El Chalten trek to Laguna Capri. Day 4: Laguna de los Tres at Mount Fitz Roy base. Day 5: Cerro Torre glacial lagoon. Day 6: Panoramic valley trail & farewell barbecue.',
         'static/images/glacier_why_us.jpg', 1, 'Exploring'),

        (4, 'Kedarkantha Winter Ridge', 'Sankri Ridge, Uttarakhand', 'Uttarakhand, India', 'Easy', 4, 350.00, 350.00, 20, 20, 4, 'Open', '2026-12-20', '2026-12-24',
         'India’s most celebrated winter summit trek. Experience knee-deep powder snow, dense pine forests, and a panoramic 360-degree Himalayan sunrise.',
         'Day 1: Drive Dehradun to Sankri base camp (6,400 ft). Day 2: Trek to Juda Ka Talab frozen lake campsite. Day 3: Kedarkantha Basecamp to 12,500 ft summit sunrise. Day 4: Descend via Hargaon pine glades to Sankri.',
         'static/images/2.jpg', 1, 'Camp Fire'),

        (5, 'Yosemite Glacier Point Ridge', 'Sierra Nevada', 'California, USA', 'Easy', 3, 450.00, 450.00, 18, 18, 2, 'Open', '2026-11-05', '2026-11-08',
         'Hike along towering granite cliffs, ancient giant sequoias, and thunderous waterfalls in California’s most iconic national park.',
         'Day 1: Yosemite Valley orientation & Mist Trail to Nevada Fall. Day 2: Panorama Trail to Glacier Point panoramic sunset. Day 3: Taft Point fissure overlook and Sentinel Dome loop.',
         'static/images/3.jpg', 0, 'Exploring'),

        (6, 'Hampta Pass & Chandratal', 'Kullu & Spiti Valleys', 'Himachal Pradesh, India', 'Moderate', 5, 480.00, 480.00, 15, 15, 4, 'Open', '2026-11-10', '2026-11-15',
         'A dramatic shift in scenery from the emerald green valleys of Kullu to the stark, moon-like desert mountains of Spiti.',
         'Day 1: Drive Manali to Jobra, trek to Chika campsite. Day 2: River crossing to Balu Ka Ghera meadow. Day 3: Climb to 14,000 ft Hampta Pass and descend to Shea Goru. Day 4: Trek to Chatru & jeep safari to pristine Chandratal Lake. Day 5: Return to Manali.',
         'static/images/1.jpg', 1, 'Trekking'),

        (7, 'Black Forest Trail Run', 'Baden-Württemberg', 'Germany', 'Easy', 2, 280.00, 280.00, 16, 16, 3, 'Completed', '2026-09-12', '2026-09-14',
         'Lush evergreen canopy trails, fairy-tale medieval castles, and alpine river crossings in southern Germany.',
         'Day 1: Freiburg to Feldberg summit ridge. Day 2: Ravenna Gorge waterfall trail and traditional Black Forest hut retreat.',
         'static/images/4.jpg', 0, 'Adventure'),

        (8, 'Mont Blanc Alpine Traverse', 'Chamonix Valley', 'France & Switzerland', 'Hard', 9, 2100.00, 2100.00, 10, 10, None, 'Closed', None, None,
         'The premier long-distance circuit around the Mont Blanc massif through three alpine nations.',
         'Day 1: Les Houches to Refuge de Miage. Day 2: Col de la Croix du Bonhomme. Day 3: Italian border crossing to Courmayeur. Day 4-9: Grand Col Ferret and Swiss valleys back to Chamonix.',
         'static/images/5.jpg', 0, 'Adventure'),
    ]
    cur.executemany("INSERT INTO treks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)", treks_data)

    # Bookings
    bookings_data = [
        (1, 6, 1, '2026-11-20', 2, 3700.00, 'Confirmed', 'Need crampons and 4-season sleeping bag rentals'),
        (2, 7, 1, '2026-11-20', 1, 1850.00, 'Confirmed', 'Vegetarian meal preference'),
        (3, 8, 2, '2026-11-15', 2, 4800.00, 'Confirmed', 'Oxygen monitor & mountain guide request'),
        (4, 9, 3, '2026-12-05', 2, 3300.00, 'Confirmed', 'Glacier photography permit assistance'),
        (5, 10, 4, '2026-12-20', 3, 1050.00, 'Confirmed', 'First-time snow trekkers group'),
        (6, 6, 6, '2026-11-10', 1, 480.00,  'Confirmed', 'Solo trekker looking for tent partner'),
        (7, 11, 7, '2026-09-12', 2, 560.00,  'Completed', 'Celebrated anniversary on Feldberg peak'),
        (8, 7, 7, '2026-09-12', 1, 280.00,  'Completed', 'Trail running pace group'),
        (9, 8, 5, '2026-11-05', 1, 450.00,  'Cancelled', 'Flight rescheduling conflict'),
    ]
    cur.executemany("INSERT INTO bookings VALUES (?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)", bookings_data)

    # Transactions
    tx_data = [
        (1, 1, 'TXN-9014238', 3700.00, 'Credit Card (Visa)', 'Success'),
        (2, 2, 'TXN-9014239', 1850.00, 'Apple Pay',         'Success'),
        (3, 3, 'TXN-9014240', 4800.00, 'UPI / NetBanking',   'Success'),
        (4, 4, 'TXN-9014241', 3300.00, 'PayPal Express',     'Success'),
        (5, 5, 'TXN-9014242', 1050.00, 'Credit Card (Master)','Success'),
        (6, 6, 'TXN-9014243', 480.00,  'UPI / NetBanking',   'Success'),
        (7, 7, 'TXN-8900112', 560.00,  'Credit Card (Visa)', 'Success'),
        (8, 8, 'TXN-8900113', 280.00,  'Apple Pay',         'Success'),
        (9, 9, 'TXN-9014250', 450.00,  'PayPal Express',     'Refunded'),
    ]
    cur.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)", tx_data)

    # Shops
    shops_data = [
        (1, 'Summit Alpine Gear Rentals', 'Gear Rental', '64.1466° N, 21.9426° W', '+354-555-8821', 4.9, 'Professional mountaineering boots, crampons, GORE-TEX jackets, and lightweight carbon poles.', 'static/images/iceland_hiking.jpg', 1),
        (2, 'Glacier Shot Photo Studio',   'Photography', '64.1282° N, 21.9114° W', '+354-555-8899', 4.8, 'Drone photography packages, cold-weather lens filters, and summit action photography.', 'static/images/iceland_hiking.jpg', 1),
        (3, 'Sherpa Craft Souvenirs',      'Souvenir',    '27.8069° N, 86.7140° E', '+977-98114400', 4.9, 'Authentic yak wool shawls, hand-beaten singing bowls, and prayer flags blessed at Tengboche.', 'static/images/6.jpg', 2),
        (4, 'Khumbu High Altitude Pharmacy','Medical & Essentials','27.8041° N, 86.7132° E','+977-98114455', 5.0, 'Diamox altitude pills, portable pulse oximeters, emergency thermal bivouacs, and first aid kits.', 'static/images/6.jpg', 2),
        (5, 'Patagonia Glacier Outpost',   'Gear Rental', '50.3380° S, 72.2648° W', '+54-2902-4911', 4.8, 'Technical ice axes, helmet kits, waterproof gaiters, and 65L expedition rucksacks.', 'static/images/glacier_why_us.jpg', 3),
        (6, 'Fitz Roy Mountain Bakery',    'Food & Cafe', '49.3315° S, 72.8860° W', '+54-2902-4920', 4.7, 'Fresh sourdough, artisanal dulce de leche pastries, hot espresso, and high-calorie trail rations.', 'static/images/glacier_why_us.jpg', 3),
        (7, 'Himalayan Nomads Camp Hub',   'Gear Rental', '31.0722° N, 78.1819° E', '+91-9877665544', 4.9, 'Zero-degree subzero down jackets, gaiters, micro-spikes, and Quechua winter tents.', 'static/images/2.jpg', 4),
        (8, 'Sankri Local Honey & Wool',   'Souvenir',    '31.0730° N, 78.1825° E', '+91-9877665599', 4.8, 'Pure mountain wild forest honey, hand-knitted Himalayan beanies, and dried wild herbs.', 'static/images/2.jpg', 4),
    ]
    cur.executemany("INSERT INTO shops VALUES (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)", shops_data)

    # Rescue Operations
    rescue_data = [
        (1, 6, 2, 2, 'Medical (AMS / Acute Altitude Sickness)', '27.9542° N, 86.8211° E (Alt: 4,920m)', 'In Progress', 'Trekker developed severe headache and nausea at Dingboche. Staff Tenzing initiated supplemental oxygen descent to 3,800m.'),
        (2, 10, 4, 4, 'Lost Trail / Low Visibility Snow Blizzard', '31.0850° N, 78.1920° E (Alt: 3,200m)', 'Resolved', 'Party of 3 took wrong detour near Juda Ka Talab lake during whiteout. Staff Ravi deployed GPS beacon guide and escorted party safely to basecamp.'),
        (3, 8, 3, 3, 'Sprained Ankle / Minor Fracture', '49.2711° S, 72.9510° W (Alt: 1,150m)', 'Resolved', 'Evacuated from Laguna de los Tres trail via packhorse support. Treated at El Chalten clinic.'),
    ]
    cur.executemany("INSERT INTO rescue_operations VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP,?,?,CURRENT_TIMESTAMP)", rescue_data)

    # Reviews
    reviews_data = [
        (1, 6, 1, 5, 'The Iceland Fjords expedition was unlike anything I have ever seen. Standing atop volcanic ridges with steam rising while glaciers gleam in the distance was awe-inspiring! Professional guides, 10/10.', 1),
        (2, 7, 1, 5, 'Flawless logistics, incredible food at basecamp, and top-tier safety. The gear rental service from Summit Alpine was pristine.', 1),
        (3, 8, 2, 5, 'Everest Base Camp was a life-long dream come true. Tenzing and the team made sure our acclimatization was perfect. Standing before Nuptse and Khumbu Icefall took my breath away.', 1),
        (4, 9, 3, 5, 'Walking on Perito Moreno glacier with crampons is surreal. The deep blue ice crevices and booming serac collapses will stay with me forever.', 1),
        (5, 10, 4, 5, 'Kedarkantha winter trek was our group’s first Himalayan snow trek. The 360-degree summit sunrise view over Swargarohini and Black Peak was magical! Friendly guides and delicious hot meals.', 1),
        (6, 11, 7, 5, 'Completed the Black Forest trail run with my partner. Stunning scenery, well-marked paths, and the mountain hut was so cozy.', 1),
    ]
    cur.executemany("INSERT INTO reviews VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)", reviews_data)


def get_db():
    engine = detect_engine()
    try:
        from flask import has_app_context
        in_ctx = has_app_context()
    except Exception:
        in_ctx = False

    if in_ctx:
        if "db" not in g:
            if engine == "postgres":
                g.db = psycopg2.connect(
                    dbname=DB_NAME, cursor_factory=psycopg2.extras.RealDictCursor, **DB_CONFIG
                )
            else:
                conn = sqlite3.connect(SQLITE_DB_PATH)
                conn.row_factory = sqlite3.Row
                g.db = conn
        return g.db
    else:
        if engine == "postgres":
            return psycopg2.connect(
                dbname=DB_NAME, cursor_factory=psycopg2.extras.RealDictCursor, **DB_CONFIG
            )
        else:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    db = get_db()
    engine = detect_engine()
    if engine == "sqlite":
        # Convert %s to ? and ILIKE to LIKE for SQLite
        adapted_sql = re.sub(r"%s", "?", sql)
        adapted_sql = re.sub(r"\bILIKE\b", "LIKE", adapted_sql, flags=re.IGNORECASE)
        cur = db.cursor()
        cur.execute(adapted_sql, args)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        if one:
            return rows[0] if rows else None
        return rows
    else:
        cur = db.cursor()
        cur.execute(sql, args)
        rows = cur.fetchall()
        cur.close()
        if one:
            return rows[0] if rows else None
        return rows


def execute(sql, args=()):
    db = get_db()
    engine = detect_engine()
    if engine == "sqlite":
        adapted_sql = re.sub(r"%s", "?", sql)
        adapted_sql = re.sub(r"\bILIKE\b", "LIKE", adapted_sql, flags=re.IGNORECASE)
        cur = db.cursor()
        cur.execute(adapted_sql, args)
        count = cur.rowcount
        cur.close()
        return count
    else:
        cur = db.cursor()
        cur.execute(sql, args)
        count = cur.rowcount
        cur.close()
        return count


def execute_insert_returning_id(sql, args=()):
    db = get_db()
    engine = detect_engine()
    if engine == "sqlite":
        adapted_sql = re.sub(r"%s", "?", sql)
        adapted_sql = re.sub(r"\s+RETURNING\s+id\s*$", "", adapted_sql, flags=re.IGNORECASE)
        cur = db.cursor()
        cur.execute(adapted_sql, args)
        last_id = cur.lastrowid
        cur.close()
        return last_id
    else:
        cur = db.cursor()
        if "RETURNING id" not in sql.upper():
            sql += " RETURNING id"
        cur.execute(sql, args)
        row = cur.fetchone()
        cur.close()
        return row["id"] if row else None


def commit():
    get_db().commit()


def rollback():
    get_db().rollback()
