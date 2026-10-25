-- Sample Data for Trekking Management System
-- Admin password: admin123 | Everyone else: pass123

-- 1. USERS
INSERT INTO users (name, username, email, contact, emergency_contact_name, emergency_contact_phone, password_hash, role, status) VALUES
('Alexander Vance',  'admin',  'admin@mountains.expedition', '+1-555-0199', 'Sarah Vance',     '+1-555-0198', 'pbkdf2:sha256:1000000$aeWGCxYs1exlBdzZ$808c7a1047bd1d52784959225400bac0c2c73bc0c9f8389f0fc9bf2d3360d0c9', 'admin', 'approved'),
('Tenzing Norgay',   'tenzing', 'tenzing@mountains.expedition', '+977-98110011', 'Pasang Lhamu',  '+977-98110012', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'staff', 'approved'),
('Elena Rostova',    'elena',   'elena@mountains.expedition',   '+41-79-555123',  'Dmitri Rostov', '+41-79-555124', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'staff', 'approved'),
('Ravi Sharma',      'ravi',    'ravi@mountains.expedition',    '+91-9822334455', 'Pooja Sharma',  '+91-9822334456', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'staff', 'approved'),
('Marco Rossi',      'marco',   'marco@mountains.expedition',   '+39-333-123456', 'Sofia Rossi',   '+39-333-123457', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'staff', 'pending'),
('Liam Hemsworth',   'liam',    'liam.h@adventurer.io',         '+1-415-8901234', 'Karen Hemsworth','+1-415-8901235', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
('Aria Stark',       'aria',    'aria.stark@winterfell.org',    '+44-7700-90012', 'Ned Stark',     '+44-7700-90013', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
('David Miller',     'david',   'david.miller@globaltrek.com',  '+1-212-7894561', 'Lisa Miller',   '+1-212-7894562', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
('Chloe Bennett',    'chloe',   'chloe.b@wanderlust.net',       '+61-491-570156', 'James Bennett', '+61-491-570157', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
('Aarav Patel',      'aarav',   'aarav.patel@himalayas.in',     '+91-9988776655', 'Sunita Patel',  '+91-9988776656', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
('Maya Lin',         'maya',    'maya.lin@summitclub.com',      '+1-604-5550188', 'Wei Lin',       '+1-604-5550189', 'pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'approved'),
('Julian Fischer',   'julian',  'julian.f@alpinist.de',         '+49-170-1234567','Ursula Fischer', '+49-170-1234568','pbkdf2:sha256:1000000$tb6NSC0pUd1UgyiQ$7be23954111005a2a3f674a382faffd40e0d6a498b1ef5409d6c84000f285438', 'user',  'blacklisted');

-- 2. TREKS
INSERT INTO treks (id, name, destination, location, difficulty, duration, base_cost, price, max_capacity, total_slots, assigned_staff_id, status, start_date, end_date, description, itinerary, image_url, is_trending, category) VALUES
(1, 'Iceland Hiking Trips', 'Iceland Fjords & Highlands', 'Iceland', 'Hard', 7, 1850.00, 1850.00, 16, 16, 3, 'Open', '2026-11-20', '2026-11-27',
    'Conquer the dramatic volcanic ridges and glacial valleys of southern Iceland. An adrenaline-filled trek crossing lava fields and geothermal springs.',
    'Day 1: Reykjavik Basecamp briefing & gear check. Day 2: Landmannalaugar geothermal fields. Day 3: Hrafntinnusker high pass snow crossing. Day 4: Lake Alftavatn glacial crossing. Day 5: Emstrur volcanic canyons. Day 6: Thorsmork birch valley summit. Day 7: Skogar waterfalls & hot springs celebration.',
    'static/images/iceland_hiking.jpg', TRUE, 'Adventure'),

(2, 'Everest High Pass Expedition', 'Khumbu Valley', 'Nepal', 'Hard', 12, 2400.00, 2400.00, 12, 12, 2, 'Open', '2026-11-15', '2026-11-27',
    'Ascend into the roof of the world through rhododendron forests, suspension bridges, and dramatic high altitude Himalayan glacial moraines.',
    'Day 1-2: Flight to Lukla & trek to Namche Bazaar. Day 3: Acclimatization hike to Everest View Hotel. Day 4: Tengboche monastery blessing. Day 5: Dingboche alpine plateau. Day 6: Lobuche glacier edge. Day 7: Everest Base Camp & Kala Patthar 5,545m sunrise. Day 8-12: Descent via Pangboche & return flight.',
    'static/images/6.jpg', TRUE, 'Trekking'),

(3, 'Patagonia Glacial Traverse', 'Perito Moreno & Fitz Roy', 'Patagonia, Argentina', 'Moderate', 6, 1650.00, 1650.00, 14, 14, 3, 'Open', '2026-12-05', '2026-12-11',
    'Witness gargantuan turquoise icebergs, sheer granite towers, and untouched glacial lakes on this once-in-a-lifetime South American pilgrimage.',
    'Day 1: El Calafate welcome dinner. Day 2: Perito Moreno ice walk with crampons. Day 3: El Chalten trek to Laguna Capri. Day 4: Laguna de los Tres at Mount Fitz Roy base. Day 5: Cerro Torre glacial lagoon. Day 6: Panoramic valley trail & farewell barbecue.',
    'static/images/glacier_why_us.jpg', TRUE, 'Exploring'),

(4, 'Kedarkantha Winter Ridge', 'Sankri Ridge, Uttarakhand', 'Uttarakhand, India', 'Easy', 4, 350.00, 350.00, 20, 20, 4, 'Open', '2026-12-20', '2026-12-24',
    'India’s most celebrated winter summit trek. Experience knee-deep powder snow, dense pine forests, and a panoramic 360-degree Himalayan sunrise.',
    'Day 1: Drive Dehradun to Sankri base camp (6,400 ft). Day 2: Trek to Juda Ka Talab frozen lake campsite. Day 3: Kedarkantha Basecamp to 12,500 ft summit sunrise. Day 4: Descend via Hargaon pine glades to Sankri.',
    'static/images/2.jpg', TRUE, 'Camp Fire'),

(5, 'Yosemite Glacier Point Ridge', 'Sierra Nevada', 'California, USA', 'Easy', 3, 450.00, 450.00, 18, 18, 2, 'Open', '2026-11-05', '2026-11-08',
    'Hike along towering granite cliffs, ancient giant sequoias, and thunderous waterfalls in California’s most iconic national park.',
    'Day 1: Yosemite Valley orientation & Mist Trail to Nevada Fall. Day 2: Panorama Trail to Glacier Point panoramic sunset. Day 3: Taft Point fissure overlook and Sentinel Dome loop.',
    'static/images/3.jpg', FALSE, 'Exploring'),

(6, 'Hampta Pass & Chandratal', 'Kullu & Spiti Valleys', 'Himachal Pradesh, India', 'Moderate', 5, 480.00, 480.00, 15, 15, 4, 'Open', '2026-11-10', '2026-11-15',
    'A dramatic shift in scenery from the emerald green valleys of Kullu to the stark, moon-like desert mountains of Spiti.',
    'Day 1: Drive Manali to Jobra, trek to Chika campsite. Day 2: River crossing to Balu Ka Ghera meadow. Day 3: Climb to 14,000 ft Hampta Pass and descend to Shea Goru. Day 4: Trek to Chatru & jeep safari to pristine Chandratal Lake. Day 5: Return to Manali.',
    'static/images/1.jpg', TRUE, 'Trekking'),

(7, 'Black Forest Trail Run', 'Baden-Württemberg', 'Germany', 'Easy', 2, 280.00, 280.00, 16, 16, 3, 'Completed', '2026-09-12', '2026-09-14',
    'Lush evergreen canopy trails, fairy-tale medieval castles, and alpine river crossings in southern Germany.',
    'Day 1: Freiburg to Feldberg summit ridge. Day 2: Ravenna Gorge waterfall trail and traditional Black Forest hut retreat.',
    'static/images/4.jpg', FALSE, 'Adventure'),

(8, 'Mont Blanc Alpine Traverse', 'Chamonix Valley', 'France & Switzerland', 'Hard', 9, 2100.00, 2100.00, 10, 10, NULL, 'Closed', NULL, NULL,
    'The premier long-distance circuit around the Mont Blanc massif through three alpine nations.',
    'Day 1: Les Houches to Refuge de Miage. Day 2: Col de la Croix du Bonhomme. Day 3: Italian border crossing to Courmayeur. Day 4-9: Grand Col Ferret and Swiss valleys back to Chamonix.',
    'static/images/5.jpg', FALSE, 'Adventure');

SELECT setval('treks_id_seq', (SELECT MAX(id) FROM treks));

-- 3. BOOKINGS
INSERT INTO bookings (id, user_id, trek_id, travel_date, num_participants, total_price, status, special_requests) VALUES
(1, 6, 1, '2026-11-20', 2, 3700.00, 'Confirmed', 'Need crampons and 4-season sleeping bag rentals'),
(2, 7, 1, '2026-11-20', 1, 1850.00, 'Confirmed', 'Vegetarian meal preference'),
(3, 8, 2, '2026-11-15', 2, 4800.00, 'Confirmed', 'Oxygen monitor & mountain guide request'),
(4, 9, 3, '2026-12-05', 2, 3300.00, 'Confirmed', 'Glacier photography permit assistance'),
(5, 10, 4, '2026-12-20', 3, 1050.00, 'Confirmed', 'First-time snow trekkers group'),
(6, 6, 6, '2026-11-10', 1, 480.00,  'Confirmed', 'Solo trekker looking for tent partner'),
(7, 11, 7, '2026-09-12', 2, 560.00,  'Completed', 'Celebrated anniversary on Feldberg peak'),
(8, 7, 7, '2026-09-12', 1, 280.00,  'Completed', 'Trail running pace group'),
(9, 8, 5, '2026-11-05', 1, 450.00,  'Cancelled', 'Flight rescheduling conflict');

SELECT setval('bookings_id_seq', (SELECT MAX(id) FROM bookings));

-- 4. TRANSACTIONS
INSERT INTO transactions (booking_id, transaction_id, amount, payment_method, status) VALUES
(1, 'TXN-9014238', 3700.00, 'Credit Card (Visa)', 'Success'),
(2, 'TXN-9014239', 1850.00, 'Apple Pay',         'Success'),
(3, 'TXN-9014240', 4800.00, 'UPI / NetBanking',   'Success'),
(4, 'TXN-9014241', 3300.00, 'PayPal Express',     'Success'),
(5, 'TXN-9014242', 1050.00, 'Credit Card (Master)','Success'),
(6, 'TXN-9014243', 480.00,  'UPI / NetBanking',   'Success'),
(7, 'TXN-8900112', 560.00,  'Credit Card (Visa)', 'Success'),
(8, 'TXN-8900113', 280.00,  'Apple Pay',         'Success'),
(9, 'TXN-9014250', 450.00,  'PayPal Express',     'Refunded');

-- 5. SHOPS
INSERT INTO shops (name, category, coordinates, contact_number, rating, description, image_url, trek_id) VALUES
('Summit Alpine Gear Rentals', 'Gear Rental',        '64.1466° N, 21.9426° W', '+354-555-8821', 4.9, 'Professional mountaineering boots, crampons, GORE-TEX jackets, and lightweight carbon poles.', 'static/images/iceland_hiking.jpg', 1),
('Glacier Shot Photo Studio',   'Photography',        '64.1282° N, 21.9114° W', '+354-555-8899', 4.8, 'Drone photography packages, cold-weather lens filters, and summit action photography.', 'static/images/iceland_hiking.jpg', 1),
('Sherpa Craft Souvenirs',      'Souvenir',           '27.8069° N, 86.7140° E', '+977-98114400', 4.9, 'Authentic yak wool shawls, hand-beaten singing bowls, and prayer flags blessed at Tengboche.', 'static/images/6.jpg', 2),
('Khumbu High Altitude Pharmacy','Medical & Essentials','27.8041° N, 86.7132° E','+977-98114455', 5.0, 'Diamox altitude pills, portable pulse oximeters, emergency thermal bivouacs, and first aid kits.', 'static/images/6.jpg', 2),
('Patagonia Glacier Outpost',   'Gear Rental',        '50.3380° S, 72.2648° W', '+54-2902-4911', 4.8, 'Technical ice axes, helmet kits, waterproof gaiters, and 65L expedition rucksacks.', 'static/images/glacier_why_us.jpg', 3),
('Fitz Roy Mountain Bakery',    'Food & Cafe',        '49.3315° S, 72.8860° W', '+54-2902-4920', 4.7, 'Fresh sourdough, artisanal dulce de leche pastries, hot espresso, and high-calorie trail rations.', 'static/images/glacier_why_us.jpg', 3),
('Himalayan Nomads Camp Hub',   'Gear Rental',        '31.0722° N, 78.1819° E', '+91-9877665544', 4.9, 'Zero-degree subzero down jackets, gaiters, micro-spikes, and Quechua winter tents.', 'static/images/2.jpg', 4),
('Sankri Local Honey & Wool',   'Souvenir',           '31.0730° N, 78.1825° E', '+91-9877665599', 4.8, 'Pure mountain wild forest honey, hand-knitted Himalayan beanies, and dried wild herbs.', 'static/images/2.jpg', 4);

-- 6. RESCUE_OPERATIONS
INSERT INTO rescue_operations (trekker_id, staff_id, trek_id, emergency_type, last_coordinates, alert_time, status, notes) VALUES
(6, 2, 2, 'Medical (AMS / Acute Altitude Sickness)', '27.9542° N, 86.8211° E (Alt: 4,920m)', NOW() - INTERVAL '3 hours', 'In Progress', 'Trekker developed severe headache and nausea at Dingboche. Staff Tenzing initiated supplemental oxygen descent to 3,800m.'),
(10, 4, 4, 'Lost Trail / Low Visibility Snow Blizzard', '31.0850° N, 78.1920° E (Alt: 3,200m)', NOW() - INTERVAL '1 day', 'Resolved', 'Party of 3 took wrong detour near Juda Ka Talab lake during whiteout. Staff Ravi deployed GPS beacon guide and escorted party safely to basecamp.'),
(8, 3, 3, 'Sprained Ankle / Minor Fracture', '49.2711° S, 72.9510° W (Alt: 1,150m)', NOW() - INTERVAL '5 days', 'Resolved', 'Evacuated from Laguna de los Tres trail via packhorse support. Treated at El Chalten clinic.');

-- 7. REVIEWS
INSERT INTO reviews (user_id, trek_id, rating, comment, is_featured) VALUES
(6, 1, 5, 'The Iceland Fjords expedition was unlike anything I have ever seen. Standing atop volcanic ridges with steam rising while glaciers gleam in the distance was awe-inspiring! Professional guides, 10/10.', TRUE),
(7, 1, 5, 'Flawless logistics, incredible food at basecamp, and top-tier safety. The gear rental service from Summit Alpine was pristine.', TRUE),
(8, 2, 5, 'Everest Base Camp was a life-long dream come true. Tenzing and the team made sure our acclimatization was perfect. Standing before Nuptse and Khumbu Icefall took my breath away.', TRUE),
(9, 3, 5, 'Walking on Perito Moreno glacier with crampons is surreal. The deep blue ice crevices and booming serac collapses will stay with me forever.', TRUE),
(10, 4, 5, 'Kedarkantha winter trek was our group’s first Himalayan snow trek. The 360-degree summit sunrise view over Swargarohini and Black Peak was magical! Friendly guides and delicious hot meals.', TRUE),
(11, 7, 5, 'Completed the Black Forest trail run with my partner. Stunning scenery, well-marked paths, and the mountain hut was so cozy.', TRUE);
