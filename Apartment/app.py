from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///apartment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -------------------- DATABASE MODELS --------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'owner' or 'programmer'

class ElectricMeter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_number = db.Column(db.String(50), nullable=False)
    month_year = db.Column(db.String(10), nullable=False)
    units = db.Column(db.Float, nullable=False)
    bill_amount = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)

class SubMeter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sub_meter_number = db.Column(db.String(50), nullable=False)
    month_year = db.Column(db.String(10), nullable=False)
    units = db.Column(db.Float, nullable=False)
    bill_amount = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)

class GasMeter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_number = db.Column(db.String(50), nullable=False)
    month_year = db.Column(db.String(10), nullable=False)
    units = db.Column(db.Float, nullable=False)
    bill_amount = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)

class WaterMeter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month_year = db.Column(db.String(10), nullable=False)
    units = db.Column(db.Float, nullable=False)
    bill_amount = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    members = db.Column(db.Integer, nullable=False)
    month_year = db.Column(db.String(10), nullable=False)
    electric_bill = db.Column(db.Float, nullable=False)
    gas_bill = db.Column(db.Float, nullable=False)
    water_bill = db.Column(db.Float, nullable=False)
    maintenance_charges = db.Column(db.Float, nullable=False)
    maintenance_comments = db.Column(db.Text, nullable=True)
    rent = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, nullable=False)
    remaining_charges = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # if user and bcrypt.check_password_hash(user.password, password):
        #     login_user(user)
        #     session['user_id'] = user.id
        #     return redirect(url_for('dashboard'))
        if username == "admin" and password == '123':
            session['user_id'] = 'admin'
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
# @login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    return redirect(url_for('login'))

# ---------- DASHBOARD ----------
@app.route('/dashboard')
# @login_required
def dashboard():
    return render_template('dashboard.html')

# ---------- ADD ELECTRIC METER RECORD ----------
@app.route('/add-electric-meter', methods=['GET', 'POST'])
# @login_required
def add_electric_meter():
    if request.method == 'POST':
        meter_number = request.form['meter_number']
        month_year = request.form['month_year']
        units = float(request.form['units'])
        bill_amount = float(request.form['bill_amount'])
        comments = request.form.get('comments', '')

        new_meter = ElectricMeter(
            meter_number=meter_number,
            month_year=month_year,
            units=units,
            bill_amount=bill_amount,
            comments=comments
        )
        db.session.add(new_meter)
        db.session.commit()
        flash('Electric meter record added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_electric_meter.html')

# ---------- VIEW HISTORY ----------
@app.route('/view-history')
# @login_required
def view_history():
    electric_meters = ElectricMeter.query.all()
    gas_meters = GasMeter.query.all()
    water_meters = WaterMeter.query.all()
    tenants = Tenant.query.all()

    return render_template('view_history.html',
                           electric_meters=electric_meters,
                           gas_meters=gas_meters,
                           water_meters=water_meters,
                           tenants=tenants)

# ---------- EDIT PREVIOUS RECORDS ----------
@app.route('/edit-electric-meter/<int:id>', methods=['GET', 'POST'])
# @login_required
def edit_electric_meter(id):
    record = ElectricMeter.query.get_or_404(id)

    if request.method == 'POST':
        record.meter_number = request.form['meter_number']
        record.month_year = request.form['month_year']
        record.units = float(request.form['units'])
        record.bill_amount = float(request.form['bill_amount'])
        record.comments = request.form.get('comments', '')

        db.session.commit()
        flash('Electric meter record updated!', 'success')
        return redirect(url_for('view_history'))

    return render_template('edit_electric_meter.html', record=record)

# ---------- DELETE RECORD ----------
@app.route('/delete-electric-meter/<int:id>')
# @login_required
def delete_electric_meter(id):
    record = ElectricMeter.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('Electric meter record deleted!', 'success')
    return redirect(url_for('view_history'))

# -------------------- INITIALIZE DATABASE --------------------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)












from flask import send_file
from reportlab.pdfgen import canvas
import os

def generate_pdf(tenants):
    filename = "static/bills/tenants_bills.pdf"
    c = canvas.Canvas(filename)
    
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, "Apartment Monthly Bill Summary")
    
    y_position = 780
    for tenant in tenants:
        c.setFont("Helvetica", 10)
        text = f"{tenant.name}: Rent={tenant.rent}, Electric={tenant.electric_bill}, Gas={tenant.gas_bill}, Water={tenant.water_bill}, Total={tenant.total_amount}"
        c.drawString(100, y_position, text)
        y_position -= 20

    c.save()
    return filename

@app.route('/download_pdf')
@login_required
def download_pdf():
    tenants = Tenant.query.all()
    filename = generate_pdf(tenants)
    return send_file(filename, as_attachment=True)



def calculate_tenant_bills():
    tenants = Tenant.query.all()
    total_members = sum(tenant.members for tenant in tenants)

    # Fetch latest gas and water bills
    latest_gas = GasMeter.query.order_by(GasMeter.id.desc()).first()
    latest_water = WaterMeter.query.order_by(WaterMeter.id.desc()).first()

    if not latest_gas or not latest_water:
        flash("Gas/Water records missing!", "danger")
        return redirect(url_for('dashboard'))

    per_member_gas_cost = latest_gas.bill_amount / total_members
    per_member_water_cost = latest_water.bill_amount / total_members

    for tenant in tenants:
        gas_bill = tenant.members * per_member_gas_cost
        water_bill = tenant.members * per_member_water_cost

        tenant.gas_bill = round(gas_bill, 2)
        tenant.water_bill = round(water_bill, 2)
    
    db.session.commit()


@app.route('/add_record', methods=['GET', 'POST'])
@login_required
def add_record():
    if request.method == 'POST':
        month_year = request.form['month_year']

        # Gas Meter Readings
        tenant_gas_units = float(request.form['tenant_gas_units'])
        tenant_gas_bill = float(request.form['tenant_gas_bill'])
        owner_gas_units = float(request.form['owner_gas_units'])
        owner_gas_bill = float(request.form['owner_gas_bill'])

        new_gas_tenant = GasMeter(meter_number="Tenant Gas", month_year=month_year, units=tenant_gas_units, bill_amount=tenant_gas_bill, comments="Tenant Gas Bill")
        new_gas_owner = GasMeter(meter_number="Owner Gas", month_year=month_year, units=owner_gas_units, bill_amount=owner_gas_bill, comments="Owner Gas Bill")

        db.session.add(new_gas_tenant)
        db.session.add(new_gas_owner)

        # Water Meter Readings
        water_units = float(request.form['water_units'])
        water_bill = float(request.form['water_bill'])

        new_water_meter = WaterMeter(month_year=month_year, units=water_units, bill_amount=water_bill, comments="Water Pump Usage")

        db.session.add(new_water_meter)
        db.session.commit()

        flash('Gas and Water Records Added!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_record.html')
