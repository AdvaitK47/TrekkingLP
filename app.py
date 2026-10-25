import os
import random
from datetime import date, datetime
from functools import wraps

from flask import (Flask, render_template, redirect, url_for, request,
                   flash, session, g, abort)
from werkzeug.security import generate_password_hash, check_password_hash

from config import DB_CONFIG, DB_NAME
from db import (get_db, close_db, query, execute, commit, rollback,
                execute_insert_returning_id, detect_engine)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "trekking-expedition-secret-key-2026")


# ---------- Database Context & User Session ----------

@app.teardown_appcontext
def teardown_db(error):
    close_db(error)


class CurrentUser:
    def __init__(self, row):
        self._row = row or {}

    @property
    def is_authenticated(self):
        return bool(self._row)

    def __getattr__(self, name):
        return self._row.get(name)


@app.before_request
def load_user():
    if request.endpoint == "static":
        return
    row = None
    if session.get("user_id"):
        row = query("SELECT * FROM users WHERE id = %s", (session["user_id"],), one=True)
        if row and row.get("status") == "blacklisted":
            session.clear()
            row = None
    g.user = CurrentUser(row)
    g.all_treks_list = query("SELECT id, name, destination FROM treks ORDER BY name")


@app.context_processor
def inject_globals():
    return {
        "current_user": g.user,
        "current_date": date.today().strftime("%Y-%m-%d"),
        "db_engine": detect_engine()
    }


def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not g.user.is_authenticated or g.user.role != role:
                flash(f"Unauthorized. {role.capitalize()} privileges required.", "danger")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return wrapped
    return decorator


def to_int(value):
    return int(value) if value and str(value).strip() else None


def to_date(value):
    return value if value and str(value).strip() else None


# ---------- 1. LANDING PAGE & DISCOVERY ----------

@app.route("/")
def index():
    # Trending Treks for mockup card grid
    trending = query("""
        SELECT * FROM v_trek_availability 
        WHERE is_trending = TRUE OR id IN (1, 2, 3, 4)
        ORDER BY is_trending DESC, id ASC 
        LIMIT 4
    """)
    if not trending:
        trending = query("SELECT * FROM v_trek_availability ORDER BY id ASC LIMIT 4")

    # All active treks for dropdowns/catalogs
    all_treks = query("SELECT * FROM v_trek_availability WHERE status = 'Open' ORDER BY name")

    # Partner Shops with trek names
    shops = query("""
        SELECT s.*, t.name AS trek_name 
        FROM shops s 
        JOIN treks t ON t.id = s.trek_id 
        ORDER BY s.rating DESC
    """)

    # Customer Reviews
    reviews = query("""
        SELECT r.*, u.name AS user_name, t.name AS trek_name 
        FROM reviews r
        JOIN users u ON u.id = r.user_id
        JOIN treks t ON t.id = r.trek_id
        ORDER BY r.rating DESC, r.id DESC
        LIMIT 6
    """)

    # Filter/Search processing if provided
    q_term = request.args.get("q", "").strip()
    start_d = request.args.get("start_date", "").strip()
    end_d = request.args.get("end_date", "").strip()
    max_p = request.args.get("max_price", "").strip()

    filtered_treks = None
    if q_term or start_d or end_d or max_p:
        sql = "SELECT * FROM v_trek_availability WHERE status = 'Open'"
        params = []
        if q_term:
            sql += " AND (name ILIKE %s OR destination ILIKE %s OR location ILIKE %s)"
            params.extend([f"%{q_term}%", f"%{q_term}%", f"%{q_term}%"])
        if max_p:
            try:
                sql += " AND base_cost <= %s"
                params.append(float(max_p))
            except ValueError:
                pass
        filtered_treks = query(sql + " ORDER BY base_cost ASC", params)

    context = {
        "trending_treks": trending,
        "all_treks": all_treks,
        "shops": shops,
        "reviews": reviews,
        "search_query": q_term,
        "start_date": start_d,
        "end_date": end_d,
        "max_price": max_p,
    }
    if filtered_treks is not None:
        context["filtered_treks"] = filtered_treks

    return render_template("index.html", **context)


# ---------- 2. BOOKING FLOW & TRANSACTIONS ----------

@app.route("/book/flow", methods=["POST"])
def user_book_trek_flow():
    trek_id = to_int(request.form.get("trek_id"))
    travel_date = request.form.get("travel_date") or date.today().strftime("%Y-%m-%d")
    num_participants = int(request.form.get("num_participants", 1))
    payment_method = request.form.get("payment_method", "Credit Card (Visa/Mastercard)")
    special_requests = request.form.get("special_requests", "").strip()

    trek = query("SELECT * FROM v_trek_availability WHERE id = %s", (trek_id,), one=True)
    if not trek:
        flash("Selected trek does not exist.", "danger")
        return redirect(url_for("index"))

    if trek["available_slots"] < num_participants:
        flash(f"Only {trek['available_slots']} slot(s) remaining for {trek['name']}.", "warning")
        return redirect(url_for("index"))

    # Determine user: if not logged in, auto-attach to verified demo trekker so test works immediately!
    user_id = g.user.id if g.user.is_authenticated else 6  # Liam Hemsworth
    total_price = float(trek["base_cost"]) * num_participants

    try:
        booking_id = execute_insert_returning_id(
            """INSERT INTO bookings (user_id, trek_id, travel_date, num_participants, total_price, status, special_requests)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, trek_id, travel_date, num_participants, total_price, "Confirmed", special_requests)
        )

        txn_code = f"TXN-{random.randint(1000000, 9999999)}"
        execute(
            """INSERT INTO transactions (booking_id, transaction_id, amount, payment_method, status)
               VALUES (%s, %s, %s, %s, %s)""",
            (booking_id, txn_code, total_price, payment_method, "Success")
        )
        commit()
        flash(f"Expedition booked! Transaction #{txn_code} confirmed (${total_price:.2f}).", "success")
    except Exception as e:
        rollback()
        flash(f"Booking error: {e}", "danger")

    if g.user.is_authenticated and g.user.role == "user":
        return redirect(url_for("user_bookings"))
    return redirect(url_for("index"))


# ---------- 3. 24/7 RESCUE SOS OPERATIONS ----------

@app.route("/rescue/sos", methods=["POST"])
def rescue_sos():
    emergency_type = request.form.get("emergency_type", "Medical (AMS)")
    coordinates = request.form.get("coordinates", "Unknown coordinates").strip()
    trek_id = to_int(request.form.get("trek_id"))
    notes = request.form.get("notes", "").strip()

    trekker_id = g.user.id if g.user.is_authenticated else 6
    assigned_staff_id = None
    if trek_id:
        trek = query("SELECT assigned_staff_id FROM treks WHERE id = %s", (trek_id,), one=True)
        if trek:
            assigned_staff_id = trek.get("assigned_staff_id")
    if not assigned_staff_id:
        assigned_staff_id = 2  # Tenzing Norgay (Lead Alpine Guide)

    try:
        execute(
            """INSERT INTO rescue_operations (trekker_id, staff_id, trek_id, emergency_type, last_coordinates, status, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (trekker_id, assigned_staff_id, trek_id, emergency_type, coordinates, "Active", notes)
        )
        commit()
        flash("URGENT RESCUE SOS TRANSMITTED: High-altitude rescue team dispatched to your GPS location.", "danger")
    except Exception as e:
        rollback()
        flash(f"Failed to record SOS dispatch: {e}", "danger")

    return redirect(url_for("index"))


# ---------- 4. REVIEWS SUBMISSION ----------

@app.route("/review/submit", methods=["POST"])
def submit_review():
    trek_id = to_int(request.form.get("trek_id"))
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment", "").strip()

    user_id = g.user.id if g.user.is_authenticated else 6
    if not comment:
        flash("Please enter review comments.", "warning")
        return redirect(url_for("index") + "#reviews")

    try:
        execute(
            """INSERT INTO reviews (user_id, trek_id, rating, comment, is_featured)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, trek_id, rating, comment, True)
        )
        commit()
        flash("Thank you! Your verified trekker review has been submitted.", "success")
    except Exception as e:
        rollback()
        flash(f"Error submitting review: {e}", "danger")

    return redirect(url_for("index") + "#reviews")


# ---------- 5. AUTHENTICATION (LOGIN / REGISTER / LOGOUT) ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form["username"].strip()
        user = query("SELECT * FROM users WHERE username = %s", (username,), one=True)
        if not user or not check_password_hash(user["password_hash"], request.form["password"]):
            flash("Invalid username or password.", "danger")
            return redirect(url_for("login"))
        if user["status"] == "blacklisted":
            flash("Account blacklisted by commander.", "danger")
            return redirect(url_for("login"))
        session["user_id"] = user["id"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        role = request.form.get("role", "user")
        if role not in ("staff", "user"):
            flash("Invalid role selected.", "danger")
            return redirect(url_for("register"))
        status = "pending" if role == "staff" else "approved"
        try:
            execute(
                """INSERT INTO users (name, username, email, contact, emergency_contact_name, emergency_contact_phone, password_hash, role, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (request.form["name"].strip(), request.form["username"].strip(),
                 request.form["email"].strip(), request.form.get("contact", "").strip(),
                 request.form.get("emergency_contact_name", "").strip(),
                 request.form.get("emergency_contact_phone", "").strip(),
                 generate_password_hash(request.form["password"]), role, status)
            )
            commit()
            if role == "staff":
                flash("Staff registration received. Pending admin approval.", "info")
            else:
                flash("Registration successful. You may now log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            rollback()
            flash(f"Registration failed: That username or email may already be in use.", "danger")
            return redirect(url_for("register"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not g.user.is_authenticated:
        return redirect(url_for("login"))
    if g.user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif g.user.role == "staff":
        return redirect(url_for("staff_dashboard"))
    return redirect(url_for("user_dashboard"))


# ---------- 6. ADMIN PORTAL (ALL 7 ENTITIES) ----------

@app.route("/admin")
@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    stats = query("""
        SELECT (SELECT COUNT(*) FROM treks) AS total_treks,
               (SELECT COUNT(*) FROM users WHERE role = 'user') AS total_users,
               (SELECT COUNT(*) FROM users WHERE role = 'staff') AS total_staff,
               (SELECT COUNT(*) FROM bookings) AS total_bookings,
               (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE status = 'Success') AS total_revenue,
               (SELECT COUNT(*) FROM rescue_operations WHERE status != 'Resolved') AS total_rescues,
               (SELECT COUNT(*) FROM shops) AS total_shops,
               (SELECT COUNT(*) FROM reviews) AS total_reviews,
               (SELECT COUNT(*) FROM users WHERE role = 'staff' AND status = 'pending') AS pending_staff
    """, one=True)
    return render_template("admin/dashboard.html", **stats)


@app.route("/admin/treks")
@role_required("admin")
def admin_treks():
    return render_template("admin/treks.html", treks=query("SELECT * FROM v_trek_availability ORDER BY id"))


def staff_choices():
    return query("SELECT id, name FROM users WHERE role = 'staff' AND status = 'approved' ORDER BY name")


@app.route("/admin/treks/add", methods=["GET", "POST"])
@role_required("admin")
def admin_add_trek():
    if request.method == "POST":
        f = request.form
        try:
            execute(
                """INSERT INTO treks (name, destination, location, difficulty, duration, base_cost, price,
                                      max_capacity, total_slots, assigned_staff_id, status, start_date, end_date,
                                      description, itinerary, image_url, is_trending, category)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (f["name"].strip(), f["destination"].strip(), f["destination"].strip(), f["difficulty"],
                 int(f["duration"]), float(f["base_cost"]), float(f["base_cost"]),
                 int(f["max_capacity"]), int(f["max_capacity"]), to_int(f.get("assigned_staff_id")),
                 f["status"], to_date(f.get("start_date")), to_date(f.get("end_date")),
                 f.get("description", ""), f.get("itinerary", ""),
                 f.get("image_url", "static/images/1.jpg"),
                 f.get("is_trending") == "1", f.get("category", "Trekking"))
            )
            commit()
            flash("Trek created successfully.", "success")
            return redirect(url_for("admin_treks"))
        except Exception as e:
            rollback()
            flash(f"Error creating trek: {e}", "danger")
    return render_template("admin/trek_form.html", trek=None, staff_list=staff_choices())


@app.route("/admin/treks/edit/<int:trek_id>", methods=["GET", "POST"])
@role_required("admin")
def admin_edit_trek(trek_id):
    trek = query("SELECT * FROM v_trek_availability WHERE id = %s", (trek_id,), one=True)
    if not trek:
        abort(404)
    if request.method == "POST":
        f = request.form
        try:
            execute(
                """UPDATE treks SET name=%s, destination=%s, location=%s, difficulty=%s, duration=%s,
                          base_cost=%s, price=%s, max_capacity=%s, total_slots=%s, assigned_staff_id=%s,
                          status=%s, start_date=%s, end_date=%s, description=%s, itinerary=%s,
                          image_url=%s, is_trending=%s, category=%s
                   WHERE id=%s""",
                (f["name"].strip(), f["destination"].strip(), f["destination"].strip(), f["difficulty"],
                 int(f["duration"]), float(f["base_cost"]), float(f["base_cost"]),
                 int(f["max_capacity"]), int(f["max_capacity"]), to_int(f.get("assigned_staff_id")),
                 f["status"], to_date(f.get("start_date")), to_date(f.get("end_date")),
                 f.get("description", ""), f.get("itinerary", ""),
                 f.get("image_url", "static/images/1.jpg"),
                 f.get("is_trending") == "1", f.get("category", "Trekking"),
                 trek_id)
            )
            commit()
            flash("Trek updated successfully.", "success")
            return redirect(url_for("admin_treks"))
        except Exception as e:
            rollback()
            flash(f"Error updating trek: {e}", "danger")
    return render_template("admin/trek_form.html", trek=trek, staff_list=staff_choices())


@app.route("/admin/treks/delete/<int:trek_id>", methods=["POST"])
@role_required("admin")
def admin_delete_trek(trek_id):
    execute("DELETE FROM treks WHERE id = %s", (trek_id,))
    commit()
    flash("Trek deleted.", "info")
    return redirect(url_for("admin_treks"))


@app.route("/admin/rescue")
@role_required("admin")
def admin_rescue():
    rescues = query("SELECT * FROM v_rescue_dashboard ORDER BY alert_time DESC")
    return render_template("admin/rescue.html", rescues=rescues)


@app.route("/admin/rescue/update/<int:rescue_id>", methods=["POST"])
@role_required("admin")
def admin_update_rescue_status(rescue_id):
    new_status = request.form.get("status", "Resolved")
    execute("UPDATE rescue_operations SET status = %s WHERE id = %s", (new_status, rescue_id))
    commit()
    flash(f"Rescue alert #{rescue_id} updated to {new_status}.", "success")
    return redirect(url_for("admin_rescue"))


@app.route("/admin/transactions")
@role_required("admin")
def admin_transactions():
    txs = query("""
        SELECT tx.*, b.travel_date, u.name AS user_name, u.email AS user_email, t.name AS trek_name, t.destination
        FROM transactions tx
        JOIN bookings b ON b.id = tx.booking_id
        JOIN users u ON u.id = b.user_id
        JOIN treks t ON t.id = b.trek_id
        ORDER BY tx.created_at DESC
    """)
    total_rev = query("SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE status = 'Success'", one=True)["total"]
    return render_template("admin/transactions.html", transactions=txs, total_revenue=total_rev)


@app.route("/admin/shops")
@role_required("admin")
def admin_shops():
    shops = query("""
        SELECT s.*, t.name AS trek_name 
        FROM shops s 
        JOIN treks t ON t.id = s.trek_id 
        ORDER BY s.id
    """)
    treks = query("SELECT id, name, destination FROM treks ORDER BY name")
    return render_template("admin/shops.html", shops=shops, treks=treks)


@app.route("/admin/shops/add", methods=["POST"])
@role_required("admin")
def admin_add_shop():
    f = request.form
    execute(
        """INSERT INTO shops (name, category, coordinates, contact_number, description, trek_id)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (f["name"].strip(), f["category"], f["coordinates"].strip(),
         f.get("contact_number", "").strip(), f.get("description", "").strip(),
         int(f["trek_id"]))
    )
    commit()
    flash("Partner shop added.", "success")
    return redirect(url_for("admin_shops"))


@app.route("/admin/reviews")
@role_required("admin")
def admin_reviews():
    revs = query("SELECT * FROM v_trek_reviews ORDER BY created_at DESC")
    return render_template("admin/reviews.html", reviews=revs)


@app.route("/admin/reviews/delete/<int:review_id>", methods=["POST"])
@role_required("admin")
def admin_delete_review(review_id):
    execute("DELETE FROM reviews WHERE id = %s", (review_id,))
    commit()
    flash("Review deleted.", "info")
    return redirect(url_for("admin_reviews"))


@app.route("/admin/bookings")
@role_required("admin")
def admin_bookings():
    return render_template("admin/bookings.html",
                           bookings=query("SELECT * FROM v_booking_details ORDER BY booking_date DESC, id DESC"))


@app.route("/admin/users")
@role_required("admin")
def admin_users():
    return render_template("admin/users.html",
                           users=query("SELECT * FROM users WHERE role = 'user' ORDER BY id"))


@app.route("/admin/staff")
@role_required("admin")
def admin_staff():
    return render_template("admin/staff.html",
                           staff=query("SELECT * FROM users WHERE role = 'staff' ORDER BY id"))


@app.route("/admin/staff/approve/<int:user_id>", methods=["POST"])
@role_required("admin")
def admin_approve_staff(user_id):
    execute("UPDATE users SET status = 'approved' WHERE id = %s AND role = 'staff'", (user_id,))
    commit()
    flash("Staff member approved.", "success")
    return redirect(url_for("admin_staff"))


@app.route("/admin/staff/blacklist/<int:user_id>", methods=["POST"])
@role_required("admin")
def admin_blacklist_staff(user_id):
    execute("UPDATE users SET status = 'blacklisted' WHERE id = %s AND role = 'staff'", (user_id,))
    commit()
    flash("Staff member blacklisted.", "warning")
    return redirect(url_for("admin_staff"))


@app.route("/admin/staff/reinstate/<int:user_id>", methods=["POST"])
@role_required("admin")
def admin_reinstate_staff(user_id):
    execute("UPDATE users SET status = 'approved' WHERE id = %s AND role = 'staff'", (user_id,))
    commit()
    flash("Staff member reinstated.", "success")
    return redirect(url_for("admin_staff"))


@app.route("/admin/users/blacklist/<int:user_id>", methods=["POST"])
@role_required("admin")
def admin_blacklist_user(user_id):
    execute("UPDATE users SET status = 'blacklisted' WHERE id = %s AND role = 'user'", (user_id,))
    commit()
    flash("Trekker blacklisted.", "warning")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/reinstate/<int:user_id>", methods=["POST"])
@role_required("admin")
def admin_reinstate_user(user_id):
    execute("UPDATE users SET status = 'approved' WHERE id = %s AND role = 'user'", (user_id,))
    commit()
    flash("Trekker reinstated.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/search")
@role_required("admin")
def admin_search():
    q_str = request.args.get("q", "").strip()
    results = {"treks": [], "staff": [], "users": []}
    if q_str:
        like = f"%{q_str}%"
        qid = int(q_str) if q_str.isdigit() else -1
        results["treks"] = query("SELECT * FROM treks WHERE name ILIKE %s OR id = %s ORDER BY id", (like, qid))
        results["staff"] = query("SELECT * FROM users WHERE role = 'staff' AND (name ILIKE %s OR id = %s) ORDER BY id", (like, qid))
        results["users"] = query("SELECT * FROM users WHERE role = 'user' AND (name ILIKE %s OR id = %s) ORDER BY id", (like, qid))
    return render_template("admin/search.html", query=q_str, results=results)


REPORTS = [
    ("Platform Revenue by Trek (Transactions + Bookings)",
     "SUM of confirmed transactions grouped by expedition.",
     """SELECT t.name AS trek, t.destination, COUNT(b.id) AS bookings, SUM(tx.amount) AS total_revenue
FROM treks t
JOIN bookings b ON b.trek_id = t.id
JOIN transactions tx ON tx.booking_id = b.id
WHERE tx.status = 'Success'
GROUP BY t.id, t.name, t.destination
ORDER BY total_revenue DESC"""),
    ("Alpine Rescue Incidents Log",
     "Dispatches with distressed trekker and responding staff.",
     """SELECT ro.id AS alert_id, u.name AS trekker, ro.emergency_type, ro.last_coordinates,
       s.name AS assigned_staff, ro.status
FROM rescue_operations ro
JOIN users u ON u.id = ro.trekker_id
LEFT JOIN users s ON s.id = ro.staff_id
ORDER BY ro.alert_time DESC"""),
    ("Customer Review & Ratings Breakdown",
     "Trek ratings aggregation with review counts.",
     """SELECT t.name AS trek, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(r.id) AS review_count
FROM treks t
LEFT JOIN reviews r ON r.trek_id = t.id
GROUP BY t.id, t.name
ORDER BY avg_rating DESC"""),
    ("Partner Shops by Trek and Category",
     "Vendor partners linked to expeditions.",
     """SELECT t.name AS trek, s.name AS vendor, s.category, s.rating, s.contact_number
FROM shops s
JOIN treks t ON t.id = s.trek_id
ORDER BY t.name, s.rating DESC"""),
    ("Staff Assignment Workload",
     "Expeditions led by certified staff.",
     """SELECT u.name AS staff_member, COUNT(t.id) AS treks_assigned
FROM users u
LEFT JOIN treks t ON t.assigned_staff_id = u.id
WHERE u.role = 'staff' AND u.status = 'approved'
GROUP BY u.id, u.name
ORDER BY treks_assigned DESC"""),
]


@app.route("/admin/reports")
@role_required("admin")
def admin_reports():
    reports_out = []
    for title, note, sql_code in REPORTS:
        rows = query(sql_code)
        cols = list(rows[0].keys()) if rows else []
        reports_out.append({"title": title, "note": note, "sql": sql_code, "rows": rows, "columns": cols})
    return render_template("admin/reports.html", reports=reports_out)


# ---------- 7. STAFF PORTAL ----------

@app.route("/staff/dashboard")
@role_required("staff")
def staff_dashboard():
    if g.user.status != "approved":
        return render_template("staff/pending.html")
    my_treks = query("SELECT * FROM v_trek_availability WHERE assigned_staff_id = %s ORDER BY id", (g.user.id,))
    my_rescues = query("SELECT * FROM v_rescue_dashboard WHERE staff_id = %s ORDER BY alert_time DESC", (g.user.id,))
    return render_template("staff/dashboard.html", treks=my_treks, rescues=my_rescues)


@app.route("/staff/trek/<int:trek_id>/participants")
@role_required("staff")
def staff_trek_participants(trek_id):
    trek = query("SELECT * FROM v_trek_availability WHERE id = %s", (trek_id,), one=True)
    if not trek or trek["assigned_staff_id"] != g.user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("staff_dashboard"))
    bookings = query("SELECT * FROM v_booking_details WHERE trek_id = %s ORDER BY booking_date, id", (trek_id,))
    return render_template("staff/participants.html", trek=trek, bookings=bookings)


@app.route("/staff/trek/<int:trek_id>/cancel-booking/<int:booking_id>", methods=["POST"])
@role_required("staff")
def staff_cancel_booking(trek_id, booking_id):
    execute("UPDATE bookings SET status = 'Cancelled' WHERE id = %s AND trek_id = %s", (booking_id, trek_id))
    execute("UPDATE transactions SET status = 'Refunded' WHERE booking_id = %s", (booking_id,))
    commit()
    flash("Participant booking cancelled by guide.", "info")
    return redirect(url_for("staff_trek_participants", trek_id=trek_id))


@app.route("/staff/trek/<int:trek_id>/update", methods=["GET", "POST"])
@role_required("staff")
def staff_update_trek(trek_id):
    trek = query("SELECT * FROM v_trek_availability WHERE id = %s", (trek_id,), one=True)
    if not trek or trek["assigned_staff_id"] != g.user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("staff_dashboard"))
    if request.method == "POST":
        total = int(request.form["total_slots"])
        status = request.form["status"]
        execute("UPDATE treks SET total_slots = %s, max_capacity = %s, status = %s WHERE id = %s",
                (total, total, status, trek_id))
        commit()
        flash("Trek details updated.", "success")
        return redirect(url_for("staff_dashboard"))
    return render_template("staff/update_trek.html", trek=trek)


@app.route("/staff/trek/<int:trek_id>/mark/<state>", methods=["POST"])
@role_required("staff")
def staff_mark_trek(trek_id, state):
    if state == "started":
        execute("UPDATE treks SET status = 'Open' WHERE id = %s AND assigned_staff_id = %s", (trek_id, g.user.id))
    elif state == "completed":
        execute("UPDATE treks SET status = 'Completed' WHERE id = %s AND assigned_staff_id = %s", (trek_id, g.user.id))
        execute("UPDATE bookings SET status = 'Completed' WHERE trek_id = %s AND status IN ('Confirmed', 'Booked')", (trek_id,))
    commit()
    flash(f"Trek status marked as {state}.", "success")
    return redirect(url_for("staff_dashboard"))


# ---------- 8. TREKKER (USER) PORTAL ----------

@app.route("/user/dashboard")
@role_required("user")
def user_dashboard():
    available = query("SELECT * FROM v_trek_availability WHERE status = 'Open' AND available_slots > 0 ORDER BY start_date")
    mine = query("SELECT * FROM v_booking_details WHERE user_id = %s ORDER BY booking_date DESC, id DESC", (g.user.id,))
    return render_template("user/dashboard.html", available_treks=available, my_bookings=mine)


@app.route("/user/treks")
@role_required("user")
def user_treks():
    diff = request.args.get("difficulty", "")
    loc = request.args.get("location", "")
    sql = "SELECT * FROM v_trek_availability WHERE status = 'Open' AND available_slots > 0"
    params = []
    if diff:
        sql += " AND difficulty = %s"
        params.append(diff)
    if loc:
        sql += " AND (location ILIKE %s OR destination ILIKE %s)"
        params.extend([f"%{loc}%", f"%{loc}%"])
    treks = query(sql + " ORDER BY start_date", params)
    booked = {r["trek_id"] for r in query("SELECT trek_id FROM bookings WHERE user_id = %s AND status IN ('Confirmed', 'Booked')", (g.user.id,))}
    return render_template("user/treks.html", treks=treks, difficulty=diff, location=loc, already_booked_ids=booked)


@app.route("/user/treks/book/<int:trek_id>", methods=["POST"])
@role_required("user")
def user_book_trek(trek_id):
    trek = query("SELECT * FROM v_trek_availability WHERE id = %s", (trek_id,), one=True)
    if not trek or trek["available_slots"] < 1:
        flash("Sorry, this expedition has no remaining open slots.", "warning")
        return redirect(url_for("user_treks"))
    try:
        travel_date = trek.get("start_date") or date.today().strftime("%Y-%m-%d")
        b_id = execute_insert_returning_id(
            """INSERT INTO bookings (user_id, trek_id, travel_date, num_participants, total_price, status)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (g.user.id, trek_id, travel_date, 1, trek["base_cost"], "Confirmed")
        )
        tx_num = f"TXN-PORTAL-{random.randint(10000, 99999)}"
        execute(
            """INSERT INTO transactions (booking_id, amount, payment_method, status, transaction_id)
               VALUES (%s, %s, %s, %s, %s)""",
            (b_id, trek["base_cost"], "Instant Portal Booking", "Success", tx_num)
        )
        commit()
        flash(f"Confirmed! You are reserved for {trek['name']}.", "success")
    except Exception as e:
        rollback()
        flash(f"Booking error: {e}", "danger")
    return redirect(url_for("user_bookings"))


@app.route("/user/bookings")
@role_required("user")
def user_bookings():
    mine = query("SELECT * FROM v_booking_details WHERE user_id = %s ORDER BY booking_date DESC, id DESC", (g.user.id,))
    return render_template("user/bookings.html", bookings=mine)


@app.route("/user/bookings/cancel/<int:booking_id>", methods=["POST"])
@role_required("user")
def user_cancel_booking(booking_id):
    execute("UPDATE bookings SET status = 'Cancelled' WHERE id = %s AND user_id = %s", (booking_id, g.user.id))
    execute("UPDATE transactions SET status = 'Refunded' WHERE booking_id = %s", (booking_id,))
    commit()
    flash("Booking cancelled and refund initiated.", "info")
    return redirect(url_for("user_bookings"))


@app.route("/user/profile", methods=["GET", "POST"])
@role_required("user")
def user_profile():
    if request.method == "POST":
        execute(
            """UPDATE users SET name = %s, email = %s, contact = %s,
                      emergency_contact_name = %s, emergency_contact_phone = %s
               WHERE id = %s""",
            (request.form["name"].strip(), request.form.get("email", "").strip(),
             request.form.get("contact", "").strip(),
             request.form.get("emergency_contact_name", "").strip(),
             request.form.get("emergency_contact_phone", "").strip(),
             g.user.id)
        )
        commit()
        flash("Profile & emergency contact details updated.", "success")
        return redirect(url_for("user_profile"))
    return render_template("user/profile.html")


if __name__ == "__main__":
    detect_engine()
    print("=" * 60)
    print("  MOUNTAINS Expedition Management System Server")
    print("  Running at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
