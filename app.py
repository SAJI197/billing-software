import io
import os
from datetime import datetime

from flask import (
Flask, flash, redirect, render_template,
request, send_file, session, url_for
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------- INIT ----------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# SAFE SECRET KEY

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecretkey")

# DATABASE CONFIG

db_url = os.environ.get("DATABASE_URL")
if not db_url:
db_url = "sqlite:///" + os.path.join(BASE_DIR, "app.db")

# Render PostgreSQL fix

if db_url.startswith("postgres://"):
db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------

class User(db.Model):
id = db.Column(db.Integer, primary_key=True)
username = db.Column(db.String(100), unique=True, nullable=False)
password = db.Column(db.String(200), nullable=False)

class Invoice(db.Model):
id = db.Column(db.Integer, primary_key=True)
customer = db.Column(db.String(200), nullable=False)
amount = db.Column(db.Float, nullable=False, default=0)
vat = db.Column(db.Float, nullable=False, default=0)
total = db.Column(db.Float, nullable=False, default=0)
date = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------- HELPERS ----------------

def init_default_user():
username = "admin"
password = "admin123"

```
existing_user = User.query.filter_by(username=username).first()
if not existing_user:
    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()
```

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():
if request.method == "POST":
username = request.form.get("username", "").strip()
password = request.form.get("password", "")

```
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session["user"] = user.id
        return redirect(url_for("dashboard"))

    flash("Invalid credentials")

return render_template("login.html")
```

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
if "user" not in session:
return redirect(url_for("login"))

```
total_sales = db.session.query(func.sum(Invoice.total)).scalar() or 0
total_vat = db.session.query(func.sum(Invoice.vat)).scalar() or 0
invoice_count = db.session.query(func.count(Invoice.id)).scalar() or 0

invoices = Invoice.query.order_by(Invoice.id.desc()).all()

return render_template(
    "dashboard.html",
    invoices=invoices,
    total_sales=total_sales,
    total_vat=total_vat,
    invoice_count=invoice_count
)
```

# ---------------- ADD INVOICE ----------------

@app.route("/add", methods=["POST"])
def add_invoice():
if "user" not in session:
return redirect(url_for("login"))

```
customer = request.form.get("customer", "").strip()
amount_text = request.form.get("amount", "0").strip()

try:
    amount = float(amount_text)
except ValueError:
    flash("Invalid amount")
    return redirect(url_for("dashboard"))

vat = round(amount * 0.05, 2)
total = round(amount + vat, 2)

inv = Invoice(
    customer=customer,
    amount=amount,
    vat=vat,
    total=total
)

db.session.add(inv)
db.session.commit()

flash("Invoice added successfully")
return redirect(url_for("dashboard"))
```

# ---------------- PDF INVOICE ----------------

@app.route("/invoice/[int:id](int:id)")
def generate_invoice(id):
if "user" not in session:
return redirect(url_for("login"))

```
inv = Invoice.query.get_or_404(id)

buffer = io.BytesIO()
c = canvas.Canvas(buffer, pagesize=A4)

y = 800
line_gap = 20

c.setFont("Helvetica-Bold", 16)
c.drawString(50, y, "TAX INVOICE")
y -= 40

c.setFont("Helvetica", 11)
c.drawString(50, y, f"Customer: {inv.customer}")
y -= line_gap

c.drawString(50, y, f"Invoice No: {inv.id}")
y -= line_gap

c.drawString(50, y, f"Date: {inv.date.strftime('%d-%m-%Y')}")
y -= line_gap

c.drawString(50, y, f"Amount: AED {inv.amount:.2f}")
y -= line_gap

c.drawString(50, y, f"VAT (5%): AED {inv.vat:.2f}")
y -= line_gap

c.drawString(50, y, f"Total: AED {inv.total:.2f}")

c.save()
buffer.seek(0)

return send_file(
    buffer,
    as_attachment=True,
    download_name=f"invoice_{inv.id}.pdf",
    mimetype="application/pdf"
)
```

# ---------------- LOGOUT ----------------import io
import os
from datetime import datetime

from flask import (
Flask, flash, redirect, render_template,
request, send_file, session, url_for
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------- INIT ----------------

BASE_DIR = os.path.abspath(os.path.dirname(**file**))

app = Flask(**name**)

# SAFE SECRET KEY

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecretkey")

# DATABASE CONFIG

db_url = os.environ.get("DATABASE_URL")
if not db_url:
db_url = "sqlite:///" + os.path.join(BASE_DIR, "app.db")

# Render PostgreSQL fix

if db_url.startswith("postgres://"):
db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------

class User(db.Model):
id = db.Column(db.Integer, primary_key=True)
username = db.Column(db.String(100), unique=True, nullable=False)
password = db.Column(db.String(200), nullable=False)

class Invoice(db.Model):
id = db.Column(db.Integer, primary_key=True)
customer = db.Column(db.String(200), nullable=False)
amount = db.Column(db.Float, nullable=False, default=0)
vat = db.Column(db.Float, nullable=False, default=0)
total = db.Column(db.Float, nullable=False, default=0)
date = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------- HELPERS ----------------

def init_default_user():
username = "admin"
password = "admin123"

```
existing_user = User.query.filter_by(username=username).first()
if not existing_user:
    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()
```

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():
if request.method == "POST":
username = request.form.get("username", "").strip()
password = request.form.get("password", "")

```
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session["user"] = user.id
        return redirect(url_for("dashboard"))

    flash("Invalid credentials")

return render_template("login.html")
```

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
if "user" not in session:
return redirect(url_for("login"))

```
total_sales = db.session.query(func.sum(Invoice.total)).scalar() or 0
total_vat = db.session.query(func.sum(Invoice.vat)).scalar() or 0
invoice_count = db.session.query(func.count(Invoice.id)).scalar() or 0

invoices = Invoice.query.order_by(Invoice.id.desc()).all()

return render_template(
    "dashboard.html",
    invoices=invoices,
    total_sales=total_sales,
    total_vat=total_vat,
    invoice_count=invoice_count
)
```

# ---------------- ADD INVOICE ----------------

@app.route("/add", methods=["POST"])
def add_invoice():
if "user" not in session:
return redirect(url_for("login"))

```
customer = request.form.get("customer", "").strip()
amount_text = request.form.get("amount", "0").strip()

try:
    amount = float(amount_text)
except ValueError:
    flash("Invalid amount")
    return redirect(url_for("dashboard"))

vat = round(amount * 0.05, 2)
total = round(amount + vat, 2)

inv = Invoice(
    customer=customer,
    amount=amount,
    vat=vat,
    total=total
)

db.session.add(inv)
db.session.commit()

flash("Invoice added successfully")
return redirect(url_for("dashboard"))
```

# ---------------- PDF INVOICE ----------------

@app.route("/invoice/[int:id](int:id)")
def generate_invoice(id):
if "user" not in session:
return redirect(url_for("login"))

```
inv = Invoice.query.get_or_404(id)

buffer = io.BytesIO()
c = canvas.Canvas(buffer, pagesize=A4)

y = 800
line_gap = 20

c.setFont("Helvetica-Bold", 16)
c.drawString(50, y, "TAX INVOICE")
y -= 40

c.setFont("Helvetica", 11)
c.drawString(50, y, f"Customer: {inv.customer}")
y -= line_gap

c.drawString(50, y, f"Invoice No: {inv.id}")
y -= line_gap

c.drawString(50, y, f"Date: {inv.date.strftime('%d-%m-%Y')}")
y -= line_gap

c.drawString(50, y, f"Amount: AED {inv.amount:.2f}")
y -= line_gap

c.drawString(50, y, f"VAT (5%): AED {inv.vat:.2f}")
y -= line_gap

c.drawString(50, y, f"Total: AED {inv.total:.2f}")

c.save()
buffer.seek(0)

return send_file(
    buffer,
    as_attachment=True,
    download_name=f"invoice_{inv.id}.pdf",
    mimetype="application/pdf"
)
```

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
session.clear()
return redirect(url_for("login"))

# ---------------- STARTUP ----------------

with app.app_context():
db.create_all()
init_default_user()

# ---------------- RUN ----------------

if **name** == "**main**":
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
import io
import os
from datetime import datetime

from flask import (
Flask, flash, redirect, render_template,
request, send_file, session, url_for
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------- INIT ----------------

BASE_DIR = os.path.abspath(os.path.dirname(**file**))

app = Flask(**name**)

# SAFE SECRET KEY

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecretkey")

# DATABASE CONFIG

db_url = os.environ.get("DATABASE_URL")
if not db_url:
db_url = "sqlite:///" + os.path.join(BASE_DIR, "app.db")

# Render PostgreSQL fix

if db_url.startswith("postgres://"):
db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------

class User(db.Model):
id = db.Column(db.Integer, primary_key=True)
username = db.Column(db.String(100), unique=True, nullable=False)
password = db.Column(db.String(200), nullable=False)

class Invoice(db.Model):
id = db.Column(db.Integer, primary_key=True)
customer = db.Column(db.String(200), nullable=False)
amount = db.Column(db.Float, nullable=False, default=0)
vat = db.Column(db.Float, nullable=False, default=0)
total = db.Column(db.Float, nullable=False, default=0)
date = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------- HELPERS ----------------

def init_default_user():
username = "admin"
password = "admin123"

```
existing_user = User.query.filter_by(username=username).first()
if not existing_user:
    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()
```

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():
if request.method == "POST":
username = request.form.get("username", "").strip()
password = request.form.get("password", "")

```
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session["user"] = user.id
        return redirect(url_for("dashboard"))

    flash("Invalid credentials")

return render_template("login.html")
```

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
if "user" not in session:
return redirect(url_for("login"))

```
total_sales = db.session.query(func.sum(Invoice.total)).scalar() or 0
total_vat = db.session.query(func.sum(Invoice.vat)).scalar() or 0
invoice_count = db.session.query(func.count(Invoice.id)).scalar() or 0

invoices = Invoice.query.order_by(Invoice.id.desc()).all()

return render_template(
    "dashboard.html",
    invoices=invoices,
    total_sales=total_sales,
    total_vat=total_vat,
    invoice_count=invoice_count
)
```

# ---------------- ADD INVOICE ----------------

@app.route("/add", methods=["POST"])
def add_invoice():
if "user" not in session:
return redirect(url_for("login"))

```
customer = request.form.get("customer", "").strip()
amount_text = request.form.get("amount", "0").strip()

try:
    amount = float(amount_text)
except ValueError:
    flash("Invalid amount")
    return redirect(url_for("dashboard"))

vat = round(amount * 0.05, 2)
total = round(amount + vat, 2)

inv = Invoice(
    customer=customer,
    amount=amount,
    vat=vat,
    total=total
)

db.session.add(inv)
db.session.commit()

flash("Invoice added successfully")
return redirect(url_for("dashboard"))
```

# ---------------- PDF INVOICE ----------------

@app.route("/invoice/[int:id](int:id)")
def generate_invoice(id):
if "user" not in session:
return redirect(url_for("login"))

```
inv = Invoice.query.get_or_404(id)

buffer = io.BytesIO()
c = canvas.Canvas(buffer, pagesize=A4)

y = 800
line_gap = 20

c.setFont("Helvetica-Bold", 16)
c.drawString(50, y, "TAX INVOICE")
y -= 40

c.setFont("Helvetica", 11)
c.drawString(50, y, f"Customer: {inv.customer}")
y -= line_gap

c.drawString(50, y, f"Invoice No: {inv.id}")
y -= line_gap

c.drawString(50, y, f"Date: {inv.date.strftime('%d-%m-%Y')}")
y -= line_gap

c.drawString(50, y, f"Amount: AED {inv.amount:.2f}")
y -= line_gap

c.drawString(50, y, f"VAT (5%): AED {inv.vat:.2f}")
y -= line_gap

c.drawString(50, y, f"Total: AED {inv.total:.2f}")

c.save()
buffer.seek(0)

return send_file(
    buffer,
    as_attachment=True,
    download_name=f"invoice_{inv.id}.pdf",
    mimetype="application/pdf"
)
```

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
session.clear()
return redirect(url_for("login"))

# ---------------- STARTUP ----------------

with app.app_context():
db.create_all()
init_default_user()

# ---------------- RUN ----------------

if **name** == "**main**":
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


@app.route("/logout")
def logout():
session.clear()
return redirect(url_for("login"))

# ---------------- STARTUP ----------------

with app.app_context():
db.create_all()
init_default_user()

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
                                                                                             
