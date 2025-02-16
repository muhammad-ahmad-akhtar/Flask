# from flask import Flask, render_template, request

# app = Flask(__name__)

# Electric_Meters = []
# unit_cost = 0
# Sub_Meters_Units = []
# Sub_Meters_Units_P = []
# Sub_Meters_Bill = []
# Gas_Bill = 0
# DATE = 0



# @app.route("/", methods = ["GET", "POST"])
# def index():
#     return render_template("index.html")

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     email = request.form.get("email")
#     password = request.form.get("password")
#     if email == "a" and password == "1":
#         return render_template("menu.html")
#     return render_template("login.html")

# @app.route("/menu", methods=["GET", "POST"])
# def menu():
#     if "date" in request.form:
#         global DATE
#         DATE = request.form.get("date")
#         return render_template("electric.html")
#     return render_template("menu.html")

# @app.route("/electric", methods=["GET", "POST"])
# def electric():
#     if "refrence" in request.form:
#         # ------------- Main Electric Meters ------------
#         refrence = int(request.form.get("refrence"))
#         refrence_bill = int(request.form.get("refrence-bill"))
#         global unit_cost
#         unit_cost = refrence_bill/refrence
#         return render_template("sub.html")
#     return render_template("electric.html")

# @app.route("/sub-meters", methods=["GET", "POST"])
# def sub():
#     if "submotor" in request.form:
#         # ------------- Sub Electric Meters -------------
#         submeter1 = int(request.form.get("submeter1"))
#         submeter2 = int(request.form.get("submeter2"))
#         submeter3 = int(request.form.get("submeter3"))
#         submeter4 = int(request.form.get("submeter4"))
#         submeter5 = int(request.form.get("submeter5"))
#         submotor = int(request.form.get("submotor"))
#         # load previous from data base (to be implemented later-on)
#         global unit_cost
#         global Sub_Meters_Bill
#         global Sub_Meters_Units
#         Sub_Meters_Units_P = [ 10, 10, 10, 10, 10, 10 ]
#         Sub_Meters_Units = [submeter1-Sub_Meters_Units_P[0], submeter2-Sub_Meters_Units_P[1], submeter3-Sub_Meters_Units_P[2], submeter4-Sub_Meters_Units_P[3], submeter5-Sub_Meters_Units_P[4], submotor-Sub_Meters_Units_P[5]]
#         Sub_Meters_Bill = [units * unit_cost for units in Sub_Meters_Units]
#         return render_template("gas.html")
#     return render_template("sub.html")

# @app.route("/gas", methods=["GET", "POST"])
# def gas():
#     if "Bill" in request.form:
#         # ------------- Gas Main Meters -------------
#         global Gas_Bill
        
#         global unit_cost
#         global Sub_Meters_Units
#         global Sub_Meters_Bill
#         global DATE
        
#         Gas_Bill = int(request.form.get("Bill"))
#         return render_template("final.html", unit_cost=unit_cost, Sub_Meters_Units=Sub_Meters_Units, Sub_Meters_Bill=Sub_Meters_Bill, date=DATE)
#     return render_template("gas.html")


# if __name__ == "__main__":
#     app.run(debug="True", port=8000)






















































from flask import Flask, render_template, request, g, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'rent_management.db'

# ------------------
# Database Helper Functions
# ------------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    # Create tables (if they don't exist)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS RentHouses (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        members_count INTEGER NOT NULL,
        comments TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MonthlyRecords (
        id INTEGER PRIMARY KEY,
        rent_house_id INTEGER NOT NULL,
        month TEXT NOT NULL,
        gas_bill REAL NOT NULL,
        water_bill REAL NOT NULL,
        electric_bill REAL NOT NULL,
        maintenance_charges REAL NOT NULL,
        surplus_amount REAL DEFAULT 0,
        FOREIGN KEY (rent_house_id) REFERENCES RentHouses(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ElectricSubMeters (
        id INTEGER PRIMARY KEY,
        rent_house_id INTEGER NOT NULL,
        month TEXT NOT NULL,
        cumulative_reading REAL NOT NULL,
        FOREIGN KEY (rent_house_id) REFERENCES RentHouses(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SharedGasMeter (
        id INTEGER PRIMARY KEY,
        month TEXT UNIQUE NOT NULL,
        cumulative_reading REAL NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SharedWaterPumpMeter (
        id INTEGER PRIMARY KEY,
        month TEXT UNIQUE NOT NULL,
        cumulative_reading REAL NOT NULL
    );
    """)
    db.commit()

@app.before_request
def initialize():
    init_db()
    # Insert sample Rent Houses if table is empty
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM RentHouses")
    if cur.fetchone()["cnt"] == 0:
        houses = [
            ("House A", 4, "Near Main Road"),
            ("House B", 3, "Backside location"),
            ("House C", 5, "Corner house"),
            ("House D", 2, "Near market"),
            ("House E", 6, "Spacious rooms")
        ]
        cur.executemany("INSERT INTO RentHouses (name, members_count, comments) VALUES (?, ?, ?)", houses)
        db.commit()

# ------------------
# Helper Functions for Meter Readings
# ------------------
def get_previous_cumulative_reading(rent_house_id, current_month):
    """
    Returns the latest cumulative reading for a given rent house that is earlier than the current month.
    If none exists, returns 0.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT cumulative_reading FROM ElectricSubMeters
        WHERE rent_house_id = ? AND month < ?
        ORDER BY month DESC LIMIT 1
    """, (rent_house_id, current_month))
    row = cursor.fetchone()
    return row["cumulative_reading"] if row else 0

def get_previous_water_reading(current_month):
    """
    Returns the latest cumulative reading for the shared water pump meter earlier than the current month.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT cumulative_reading FROM SharedWaterPumpMeter
        WHERE month < ?
        ORDER BY month DESC LIMIT 1
    """, (current_month,))
    row = cursor.fetchone()
    return row["cumulative_reading"] if row else 0

# ------------------
# Shared Flow Data
# ------------------
# In a production app, you might store this in session data.
flow_data = {
    "DATE": "",
    "unit_cost": 0,
    "sub_meter_readings": [],   # current cumulative readings: 5 houses, 1 water pump
    "electric_usage": [],       # computed usage for 5 houses and water pump
    "Gas_reading": 0            # current cumulative reading for the gas meter
}

# ------------------
# Routes
# ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email == "a" and password == "1":
            return redirect(url_for('menu'))
        else:
            error = "Invalid credentials. Please try again."
    return render_template("login.html", error=error)

@app.route("/menu", methods=["GET", "POST"])
def menu():
    error = None
    if request.method == "POST":
        date_input = request.form.get("date")
        try:
            # Validate date format (expecting YYYY-MM)
            datetime.strptime(date_input, "%Y-%m")
            flow_data["DATE"] = date_input
            return redirect(url_for('electric'))
        except ValueError:
            error = "Invalid date format. Use YYYY-MM."
    return render_template("menu.html", error=error)

@app.route("/electric", methods=["GET", "POST"])
def electric():
    error = None
    if request.method == "POST":
        try:
            # Main electric meter: current cumulative reading and the bill amount
            reference_reading = float(request.form.get("refrence"))
            reference_bill = float(request.form.get("refrence-bill"))
            if reference_reading == 0:
                raise ValueError("Reference reading cannot be zero.")
            flow_data["unit_cost"] = reference_bill / reference_reading
            return redirect(url_for('sub_meters'))
        except Exception as e:
            error = "Error in electric meter input: " + str(e)
    return render_template("electric.html", error=error)

@app.route("/sub-meters", methods=["GET", "POST"])
def sub_meters():
    error = None
    if request.method == "POST":
        try:
            # Expect cumulative readings for 5 houses and 1 water pump
            reading1 = float(request.form.get("submeter1"))
            reading2 = float(request.form.get("submeter2"))
            reading3 = float(request.form.get("submeter3"))
            reading4 = float(request.form.get("submeter4"))
            reading5 = float(request.form.get("submeter5"))
            water_reading = float(request.form.get("submotor"))
            
            flow_data["sub_meter_readings"] = [reading1, reading2, reading3, reading4, reading5, water_reading]
            
            # Compute actual usage for each house:
            usage_list = []
            for house_id in range(1, 6):
                prev = get_previous_cumulative_reading(house_id, flow_data["DATE"])
                current = flow_data["sub_meter_readings"][house_id - 1]
                usage = current - prev
                usage_list.append(usage)
            # For water pump meter
            prev_water = get_previous_water_reading(flow_data["DATE"])
            water_usage = water_reading - prev_water
            usage_list.append(water_usage)
            
            flow_data["electric_usage"] = usage_list
            return redirect(url_for('gas'))
        except Exception as e:
            error = "Error in sub meter input: " + str(e)
    return render_template("sub.html", error=error)

@app.route("/gas", methods=["GET", "POST"])
def gas():
    error = None
    if request.method == "POST":
        try:
            # Gas meter: current cumulative reading is entered
            gas_reading = float(request.form.get("Bill"))
            flow_data["Gas_reading"] = gas_reading
            
            db = get_db()
            cur = db.cursor()
            date = flow_data["DATE"]
            
            # Insert cumulative readings for each rent house in ElectricSubMeters
            for i in range(5):
                cur.execute("""
                    INSERT INTO ElectricSubMeters (rent_house_id, month, cumulative_reading)
                    VALUES (?, ?, ?)
                """, (i + 1, date, flow_data["sub_meter_readings"][i]))
            
            # Insert cumulative reading for the shared water pump meter
            cur.execute("""
                INSERT INTO SharedWaterPumpMeter (month, cumulative_reading)
                VALUES (?, ?)
            """, (date, flow_data["sub_meter_readings"][5]))
            
            # Insert cumulative reading for the gas meter
            cur.execute("""
                INSERT INTO SharedGasMeter (month, cumulative_reading)
                VALUES (?, ?)
            """, (date, gas_reading))
            
            db.commit()
            return redirect(url_for('final'))
        except Exception as e:
            error = "Error in gas input: " + str(e)
            return render_template("gas.html", error=error)
    return render_template("gas.html", error=error)

@app.route("/final", methods=["GET"])
def final():
    db = get_db()
    cur = db.cursor()
    
    cur.execute("SELECT * FROM RentHouses")
    rent_houses = cur.fetchall()
    
    cur.execute("SELECT * FROM MonthlyRecords")
    monthly_records = cur.fetchall()
    
    cur.execute("SELECT * FROM ElectricSubMeters")
    electric_subs = cur.fetchall()
    
    cur.execute("SELECT * FROM SharedGasMeter")
    shared_gas = cur.fetchall()
    
    cur.execute("SELECT * FROM SharedWaterPumpMeter")
    shared_water = cur.fetchall()
    
    return render_template("final.html",
                           flow_data=flow_data,
                           rent_houses=rent_houses,
                           monthly_records=monthly_records,
                           electric_subs=electric_subs,
                           shared_gas=shared_gas,
                           shared_water=shared_water)

if __name__ == "__main__":
    app.run(debug=True, port=8000)
