import io
import json
import math
import os
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

try:
    from num2words import num2words
except Exception:
    num2words = None

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}",
)
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace(
        'postgres://', 'postgresql://', 1
    )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

COMPANY = {
    'name': 'TORONTO ROAD TRANSPORT LLC',
    'address': 'Dubai, UAE',
    'trn': 'TRN: 100000000000003',
    'phone': 'Phone: +971 00 000 0000',
    'email': 'Email: accounts@example.com',
    'footer': 'Powered by BAB ALFALAH',
}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, default='')
    trn = db.Column(db.String(100), default='')
    phone = db.Column(db.String(100), default='')
    email = db.Column(db.String(120), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, default='')
    trn = db.Column(db.String(100), default='')
    phone = db.Column(db.String(100), default='')
    email = db.Column(db.String(120), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer = db.relationship('Customer')
    items_json = db.Column(db.Text, nullable=False, default='[]')
    notes = db.Column(db.Text, default='')
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    vat_5_total = db.Column(db.Numeric(12, 2), default=0)
    vat_0_total = db.Column(db.Numeric(12, 2), default=0)
    vat_total = db.Column(db.Numeric(12, 2), default=0)
    grand_total = db.Column(db.Numeric(12, 2), default=0)
    asp_status = db.Column(db.String(50), default='Not Submitted')
    asp_reference = db.Column(db.String(120), default='')
    uuid_ref = db.Column(db.String(120), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doc_no = db.Column(db.String(50), unique=True, nullable=False)
    doc_date = db.Column(db.Date, nullable=False, default=date.today)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    supplier = db.relationship('Supplier')
    description = db.Column(db.Text, default='')
    taxable_amount = db.Column(db.Numeric(12, 2), default=0)
    vat_percent = db.Column(db.Numeric(5, 2), default=5)
    vat_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PaymentMade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voucher_no = db.Column(db.String(50), unique=True, nullable=False)
    voucher_date = db.Column(db.Date, nullable=False, default=date.today)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    supplier = db.relationship('Supplier')
    amount = db.Column(db.Numeric(12, 2), default=0)
    reference = db.Column(db.String(120), default='')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voucher_no = db.Column(db.String(50), unique=True, nullable=False)
    voucher_date = db.Column(db.Date, nullable=False, default=date.today)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer = db.relationship('Customer')
    amount = db.Column(db.Numeric(12, 2), default=0)
    reference = db.Column(db.String(120), default='')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CreditNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credit_no = db.Column(db.String(50), unique=True, nullable=False)
    credit_date = db.Column(db.Date, nullable=False, default=date.today)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer = db.relationship('Customer')
    invoice_ref = db.Column(db.String(50), default='')
    description = db.Column(db.Text, default='')
    taxable_amount = db.Column(db.Numeric(12, 2), default=0)
    vat_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def to_decimal(val):
    return Decimal(str(val or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def money(val):
    return f"{to_decimal(val):,.2f}"


@app.template_filter('money')
def money_filter(val):
    return money(val)


def amount_in_words(amount: Decimal) -> str:
    whole = int(amount)
    frac = int((amount - Decimal(whole)) * 100)
    if num2words:
        words = num2words(whole, to='cardinal', lang='en').title()
        if frac:
            return f"{words} Dirhams and {frac:02d}/100"
        return f"{words} Dirhams Only"
    return f"AED {money(amount)} Only"


def login_required(func_):
    @wraps(func_)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return func_(*args, **kwargs)

    return wrapper


def next_number(prefix: str, current_value: str | None) -> str:
    if current_value:
        return current_value
    last = db.session.execute(
        db.select(func.max(Invoice.id)) if prefix == 'INV' else
        db.select(func.max(Purchase.id)) if prefix == 'PUR' else
        db.select(func.max(PaymentMade.id)) if prefix == 'PAY' else
        db.select(func.max(Receipt.id)) if prefix == 'REC' else
        db.select(func.max(CreditNote.id))
    ).scalar() or 0
    return f"{prefix}-{last + 1:04d}"


def parse_invoice_items(form) -> list[dict]:
    descriptions = form.getlist('description')
    qtys = form.getlist('qty')
    rates = form.getlist('rate')
    vats = form.getlist('vat_percent')
    items = []
    for desc, qty, rate, vat in zip(descriptions, qtys, rates, vats):
        if not (desc or qty or rate):
            continue
        qty_d = to_decimal(qty)
        rate_d = to_decimal(rate)
        amount = (qty_d * rate_d).quantize(Decimal('0.01'))
        vat_pct = to_decimal(vat)
        vat_amount = (amount * vat_pct / Decimal('100')).quantize(Decimal('0.01'))
        items.append({
            'description': desc,
            'qty': str(qty_d),
            'rate': str(rate_d),
            'amount': str(amount),
            'vat_percent': str(vat_pct),
            'vat_amount': str(vat_amount),
        })
    return items


def compute_invoice_totals(items: list[dict]):
    subtotal = sum(to_decimal(i['amount']) for i in items)
    vat_5 = sum(
        to_decimal(i['vat_amount'])
        for i in items
        if to_decimal(i['vat_percent']) == Decimal('5.00')
    )
    vat_0 = sum(
        to_decimal(i['vat_amount'])
        for i in items
        if to_decimal(i['vat_percent']) == Decimal('0.00')
    )
    vat_total = vat_5 + vat_0
    grand_total = subtotal + vat_total
    return subtotal, vat_5, vat_0, vat_total, grand_total


def draw_common_header(pdf, title, doc_no, doc_date):
    width, height = A4
    pdf.setFont('Helvetica-Bold', 15)
    pdf.drawString(18 * mm, height - 18 * mm, COMPANY['name'])
    pdf.setFont('Helvetica', 9)
    pdf.drawString(18 * mm, height - 24 * mm, COMPANY['address'])
    pdf.drawString(18 * mm, height - 29 * mm, COMPANY['trn'])
    pdf.drawString(18 * mm, height - 34 * mm, COMPANY['phone'])
    pdf.drawString(18 * mm, height - 39 * mm, COMPANY['email'])

    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawRightString(width - 18 * mm, height - 18 * mm, title)
    pdf.setFont('Helvetica', 10)
    pdf.drawRightString(width - 18 * mm, height - 26 * mm, f'No: {doc_no}')
    pdf.drawRightString(width - 18 * mm, height - 32 * mm, f'Date: {doc_date.strftime("%d-%m-%Y")}')
    pdf.line(18 * mm, height - 44 * mm, width - 18 * mm, height - 44 * mm)
    return width, height


def simple_pdf(title, doc_no, doc_date, party_name, party_meta, lines):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = draw_common_header(pdf, title, doc_no, doc_date)
    y = height - 54 * mm
    pdf.setFont('Helvetica-Bold', 10)
    pdf.drawString(18 * mm, y, 'Party:')
    pdf.setFont('Helvetica', 10)
    pdf.drawString(33 * mm, y, party_name)
    y -= 6 * mm
    for line in party_meta:
        pdf.drawString(33 * mm, y, line)
        y -= 5 * mm
    y -= 5 * mm
    pdf.setFont('Helvetica', 10)
    for label, value in lines:
        pdf.drawString(18 * mm, y, f'{label}:')
        pdf.drawString(60 * mm, y, str(value))
        y -= 7 * mm
    pdf.setFont('Helvetica-Oblique', 9)
    pdf.drawString(18 * mm, 15 * mm, COMPANY['footer'])
    pdf.save()
    buffer.seek(0)
    return buffer


def invoice_pdf(invoice: Invoice):
    def clean_text(value: str) -> str:
        return ' '.join((value or '').replace(' ', ' ').replace('•', '-').split())

    def vat_percent_text(value) -> str:
        dec = to_decimal(value)
        return f"{int(dec)}%" if dec == dec.to_integral() else f"{dec.normalize()}%"

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    items = json.loads(invoice.items_json)
    per_page = 18
    pages = max(1, math.ceil(len(items) / per_page))

    left = 18 * mm
    right = width - 18 * mm
    table_width = right - left
    col_widths = [12 * mm, 76 * mm, 18 * mm, 25 * mm, 25 * mm, 16 * mm, 22 * mm]
    x_positions = [left]
    for w in col_widths:
        x_positions.append(x_positions[-1] + w)

    for page_idx in range(pages):
        draw_common_header(pdf, 'TAX INVOICE', invoice.invoice_no, invoice.invoice_date)
        y = height - 56 * mm
        pdf.setFont('Helvetica-Bold', 10)
        pdf.drawString(left, y, 'Customer:')
        pdf.setFont('Helvetica', 10)
        pdf.drawString(left + 20 * mm, y, clean_text(invoice.customer.name))
        y -= 5 * mm
        if invoice.customer.address:
            pdf.drawString(left + 20 * mm, y, clean_text(invoice.customer.address)[:80])
            y -= 5 * mm
        if invoice.customer.trn:
            pdf.drawString(left + 20 * mm, y, f'TRN: {clean_text(invoice.customer.trn)}')
            y -= 5 * mm
        y -= 4 * mm

        table_top = y
        row_h = 8 * mm
        if page_idx == pages - 1:
            table_bottom = 74 * mm
        else:
            table_bottom = 28 * mm

        headers = ['#', 'Description', 'Qty', 'Rate', 'Amount', 'VAT %', 'VAT Amt']
        pdf.setFont('Helvetica-Bold', 9)
        pdf.rect(left, table_bottom, table_width, table_top - table_bottom + row_h, stroke=1, fill=0)
        pdf.setFillGray(0.94)
        pdf.rect(left, table_top - 2 * mm, table_width, row_h, stroke=0, fill=1)
        pdf.setFillGray(0)
        for x in x_positions[1:-1]:
            pdf.line(x, table_bottom, x, table_top - 2 * mm + row_h)
        pdf.line(left, table_top - 2 * mm, right, table_top - 2 * mm)
        pdf.line(left, table_top - 2 * mm + row_h, right, table_top - 2 * mm + row_h)

        header_y = table_top + 1 * mm
        pdf.drawCentredString((x_positions[0] + x_positions[1]) / 2, header_y, headers[0])
        pdf.drawString(x_positions[1] + 2 * mm, header_y, headers[1])
        pdf.drawRightString(x_positions[3] - 2 * mm, header_y, headers[2])
        pdf.drawRightString(x_positions[4] - 2 * mm, header_y, headers[3])
        pdf.drawRightString(x_positions[5] - 2 * mm, header_y, headers[4])
        pdf.drawRightString(x_positions[6] - 2 * mm, header_y, headers[5])
        pdf.drawRightString(x_positions[7] - 2 * mm, header_y, headers[6])

        y = table_top - 2 * mm - 6 * mm
        page_items = items[page_idx * per_page:(page_idx + 1) * per_page]
        pdf.setFont('Helvetica', 9)
        for idx, item in enumerate(page_items, start=page_idx * per_page + 1):
            pdf.drawCentredString((x_positions[0] + x_positions[1]) / 2, y, str(idx))
            pdf.drawString(x_positions[1] + 2 * mm, y, clean_text(item['description'])[:42])
            pdf.drawRightString(x_positions[3] - 2 * mm, y, money(item['qty']))
            pdf.drawRightString(x_positions[4] - 2 * mm, y, money(item['rate']))
            pdf.drawRightString(x_positions[5] - 2 * mm, y, money(item['amount']))
            pdf.drawRightString(x_positions[6] - 2 * mm, y, vat_percent_text(item['vat_percent']))
            pdf.drawRightString(x_positions[7] - 2 * mm, y, money(item['vat_amount']))
            pdf.line(left, y - 2.5 * mm, right, y - 2.5 * mm)
            y -= row_h

        if page_idx == pages - 1:
            words_y = 58 * mm
            pdf.setFont('Helvetica', 10)
            pdf.drawString(left, words_y, f'Amount in words: {amount_in_words(to_decimal(invoice.grand_total))}')

            summary = [
                ('Subtotal', invoice.subtotal),
                ('VAT @ 5%', invoice.vat_5_total),
                ('VAT @ 0%', invoice.vat_0_total),
                ('VAT Total', invoice.vat_total),
                ('Grand Total', invoice.grand_total),
            ]
            label_x = 128 * mm
            value_x = right - 2 * mm
            sy = 58 * mm
            pdf.setFont('Helvetica', 10)
            for label, value in summary:
                if label == 'Grand Total':
                    pdf.setFont('Helvetica-Bold', 10)
                else:
                    pdf.setFont('Helvetica', 10)
                pdf.drawString(label_x, sy, label)
                pdf.drawRightString(value_x, sy, money(value))
                sy -= 6 * mm

        pdf.setFont('Helvetica-Oblique', 9)
        pdf.drawString(left, 15 * mm, COMPANY['footer'])
        if page_idx < pages - 1:
            pdf.showPage()

    pdf.save()
    buffer.seek(0)
    return buffer


@app.context_processor
def inject_company():
    return {'company': COMPANY}


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    return render_template(
        'dashboard.html',
        invoice_count=Invoice.query.count(),
        purchase_count=Purchase.query.count(),
        receipt_total=sum(to_decimal(r.amount) for r in Receipt.query.all()),
        payment_total=sum(to_decimal(p.amount) for p in PaymentMade.query.all()),
    )


@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    if request.method == 'POST':
        c = Customer(
            name=request.form['name'],
            address=request.form.get('address', ''),
            trn=request.form.get('trn', ''),
            phone=request.form.get('phone', ''),
            email=request.form.get('email', ''),
        )
        db.session.add(c)
        db.session.commit()
        flash('Customer added.', 'success')
        return redirect(url_for('customers'))
    return render_template('customers.html', customers=Customer.query.order_by(Customer.name).all())


@app.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    if request.method == 'POST':
        s = Supplier(
            name=request.form['name'],
            address=request.form.get('address', ''),
            trn=request.form.get('trn', ''),
            phone=request.form.get('phone', ''),
            email=request.form.get('email', ''),
        )
        db.session.add(s)
        db.session.commit()
        flash('Supplier added.', 'success')
        return redirect(url_for('suppliers'))
    return render_template('suppliers.html', suppliers=Supplier.query.order_by(Supplier.name).all())


@app.route('/invoices')
@login_required
def invoices():
    return render_template('invoices.html', invoices=Invoice.query.order_by(Invoice.id.desc()).all())


@app.route('/invoice/new', methods=['GET', 'POST'])
@login_required
def invoice_new():
    if request.method == 'POST':
        items = parse_invoice_items(request.form)
        if not items:
            flash('Add at least one line item.', 'danger')
            return redirect(url_for('invoice_new'))

        subtotal, vat_5, vat_0, vat_total, grand_total = compute_invoice_totals(items)
        inv = Invoice(
            invoice_no=request.form.get('invoice_no') or next_number('INV', None),
            invoice_date=datetime.strptime(request.form['invoice_date'], '%Y-%m-%d').date(),
            customer_id=int(request.form['customer_id']),
            items_json=json.dumps(items),
            notes=request.form.get('notes', ''),
            subtotal=subtotal,
            vat_5_total=vat_5,
            vat_0_total=vat_0,
            vat_total=vat_total,
            grand_total=grand_total,
        )
        db.session.add(inv)
        db.session.commit()
        flash('Invoice created.', 'success')
        return redirect(url_for('invoices'))

    return render_template(
        'invoice_form.html',
        customers=Customer.query.order_by(Customer.name).all(),
        invoice_no=next_number('INV', None),
        today=date.today(),
    )


@app.route('/invoice/<int:invoice_id>/pdf')
@login_required
def invoice_download(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    return send_file(
        invoice_pdf(inv),
        as_attachment=True,
        download_name=f'{inv.invoice_no}.pdf',
        mimetype='application/pdf',
    )


@app.route('/purchases', methods=['GET', 'POST'])
@login_required
def purchases():
    if request.method == 'POST':
        taxable = to_decimal(request.form['taxable_amount'])
        vat_percent = to_decimal(request.form['vat_percent'])
        vat_amount = (taxable * vat_percent / Decimal('100')).quantize(Decimal('0.01'))
        total = taxable + vat_amount
        row = Purchase(
            doc_no=request.form.get('doc_no') or next_number('PUR', None),
            doc_date=datetime.strptime(request.form['doc_date'], '%Y-%m-%d').date(),
            supplier_id=int(request.form['supplier_id']),
            description=request.form.get('description', ''),
            taxable_amount=taxable,
            vat_percent=vat_percent,
            vat_amount=vat_amount,
            total_amount=total,
        )
        db.session.add(row)
        db.session.commit()
        flash('Purchase saved.', 'success')
        return redirect(url_for('purchases'))

    return render_template(
        'purchases.html',
        purchases=Purchase.query.order_by(Purchase.id.desc()).all(),
        suppliers=Supplier.query.order_by(Supplier.name).all(),
        doc_no=next_number('PUR', None),
        today=date.today(),
    )


@app.route('/purchase/<int:row_id>/pdf')
@login_required
def purchase_pdf(row_id):
    row = Purchase.query.get_or_404(row_id)
    pdf = simple_pdf(
        'PURCHASE VOUCHER',
        row.doc_no,
        row.doc_date,
        row.supplier.name,
        [row.supplier.address, f'TRN: {row.supplier.trn}'],
        [
            ('Description', row.description),
            ('Taxable Amount', money(row.taxable_amount)),
            ('VAT %', row.vat_percent),
            ('VAT Amount', money(row.vat_amount)),
            ('Total', money(row.total_amount)),
        ],
    )
    return send_file(
        pdf,
        as_attachment=True,
        download_name=f'{row.doc_no}.pdf',
        mimetype='application/pdf',
    )


@app.route('/payments', methods=['GET', 'POST'])
@login_required
def payments():
    if request.method == 'POST':
        row = PaymentMade(
            voucher_no=request.form.get('voucher_no') or next_number('PAY', None),
            voucher_date=datetime.strptime(request.form['voucher_date'], '%Y-%m-%d').date(),
            supplier_id=int(request.form['supplier_id']),
            amount=to_decimal(request.form['amount']),
            reference=request.form.get('reference', ''),
            notes=request.form.get('notes', ''),
        )
        db.session.add(row)
        db.session.commit()
        flash('Payment saved.', 'success')
        return redirect(url_for('payments'))

    return render_template(
        'payments.html',
        payments=PaymentMade.query.order_by(PaymentMade.id.desc()).all(),
        suppliers=Supplier.query.order_by(Supplier.name).all(),
        voucher_no=next_number('PAY', None),
        today=date.today(),
    )


@app.route('/payment/<int:row_id>/pdf')
@login_required
def payment_pdf(row_id):
    row = PaymentMade.query.get_or_404(row_id)
    pdf = simple_pdf(
        'PAYMENT VOUCHER',
        row.voucher_no,
        row.voucher_date,
        row.supplier.name,
        [row.supplier.address],
        [('Amount', money(row.amount)), ('Reference', row.reference), ('Notes', row.notes)],
    )
    return send_file(
        pdf,
        as_attachment=True,
        download_name=f'{row.voucher_no}.pdf',
        mimetype='application/pdf',
    )


@app.route('/receipts', methods=['GET', 'POST'])
@login_required
def receipts():
    if request.method == 'POST':
        row = Receipt(
            voucher_no=request.form.get('voucher_no') or next_number('REC', None),
            voucher_date=datetime.strptime(request.form['voucher_date'], '%Y-%m-%d').date(),
            customer_id=int(request.form['customer_id']),
            amount=to_decimal(request.form['amount']),
            reference=request.form.get('reference', ''),
            notes=request.form.get('notes', ''),
        )
        db.session.add(row)
        db.session.commit()
        flash('Receipt saved.', 'success')
        return redirect(url_for('receipts'))

    return render_template(
        'receipts.html',
        receipts=Receipt.query.order_by(Receipt.id.desc()).all(),
        customers=Customer.query.order_by(Customer.name).all(),
        voucher_no=next_number('REC', None),
        today=date.today(),
    )


@app.route('/receipt/<int:row_id>/pdf')
@login_required
def receipt_pdf(row_id):
    row = Receipt.query.get_or_404(row_id)
    pdf = simple_pdf(
        'RECEIPT VOUCHER',
        row.voucher_no,
        row.voucher_date,
        row.customer.name,
        [row.customer.address],
        [('Amount', money(row.amount)), ('Reference', row.reference), ('Notes', row.notes)],
    )
    return send_file(
        pdf,
        as_attachment=True,
        download_name=f'{row.voucher_no}.pdf',
        mimetype='application/pdf',
    )


@app.route('/credit-notes', methods=['GET', 'POST'])
@login_required
def credit_notes():
    if request.method == 'POST':
        taxable = to_decimal(request.form['taxable_amount'])
        vat_amount = to_decimal(request.form['vat_amount'])
        row = CreditNote(
            credit_no=request.form.get('credit_no') or next_number('CRN', None),
            credit_date=datetime.strptime(request.form['credit_date'], '%Y-%m-%d').date(),
            customer_id=int(request.form['customer_id']),
            invoice_ref=request.form.get('invoice_ref', ''),
            description=request.form.get('description', ''),
            taxable_amount=taxable,
            vat_amount=vat_amount,
            total_amount=taxable + vat_amount,
        )
        db.session.add(row)
        db.session.commit()
        flash('Credit note saved.', 'success')
        return redirect(url_for('credit_notes'))

    return render_template(
        'credit_notes.html',
        credit_notes=CreditNote.query.order_by(CreditNote.id.desc()).all(),
        customers=Customer.query.order_by(Customer.name).all(),
        credit_no=next_number('CRN', None),
        today=date.today(),
    )


@app.route('/credit-note/<int:row_id>/pdf')
@login_required
def credit_note_pdf(row_id):
    row = CreditNote.query.get_or_404(row_id)
    pdf = simple_pdf(
        'CREDIT NOTE',
        row.credit_no,
        row.credit_date,
        row.customer.name,
        [row.customer.address],
        [
            ('Invoice Ref', row.invoice_ref),
            ('Description', row.description),
            ('Taxable Amount', money(row.taxable_amount)),
            ('VAT Amount', money(row.vat_amount)),
            ('Total', money(row.total_amount)),
        ],
    )
    return send_file(
        pdf,
        as_attachment=True,
        download_name=f'{row.credit_no}.pdf',
        mimetype='application/pdf',
    )


@app.route('/statement', methods=['GET'])
@login_required
def statement():
    customer_id = request.args.get('customer_id', type=int)
    customers = Customer.query.order_by(Customer.name).all()
    ledger = []
    balance = Decimal('0.00')
    customer = None

    if customer_id:
        customer = Customer.query.get_or_404(customer_id)
        invoices = Invoice.query.filter_by(customer_id=customer_id).all()
        receipts = Receipt.query.filter_by(customer_id=customer_id).all()
        credits = CreditNote.query.filter_by(customer_id=customer_id).all()

        rows = []
        for inv in invoices:
            rows.append((inv.invoice_date, inv.invoice_no, 'Invoice', to_decimal(inv.grand_total), Decimal('0.00')))
        for rec in receipts:
            rows.append((rec.voucher_date, rec.voucher_no, 'Receipt', Decimal('0.00'), to_decimal(rec.amount)))
        for cr in credits:
            rows.append((cr.credit_date, cr.credit_no, 'Credit Note', Decimal('0.00'), to_decimal(cr.total_amount)))

        for row in sorted(rows, key=lambda x: (x[0], x[1])):
            balance += row[3] - row[4]
            ledger.append(
                {
                    'date': row[0],
                    'doc_no': row[1],
                    'type': row[2],
                    'debit': row[3],
                    'credit': row[4],
                    'balance': balance,
                }
            )

    return render_template('statement.html', customers=customers, customer=customer, ledger=ledger)


@app.route('/statement/pdf')
@login_required
def statement_pdf():
    customer_id = request.args.get('customer_id', type=int)
    customer = Customer.query.get_or_404(customer_id)
    invoices = Invoice.query.filter_by(customer_id=customer_id).all()
    receipts = Receipt.query.filter_by(customer_id=customer_id).all()
    credits = CreditNote.query.filter_by(customer_id=customer_id).all()

    rows = []
    bal = Decimal('0.00')
    for inv in invoices:
        rows.append((inv.invoice_date, inv.invoice_no, 'Invoice', to_decimal(inv.grand_total), Decimal('0.00')))
    for rec in receipts:
        rows.append((rec.voucher_date, rec.voucher_no, 'Receipt', Decimal('0.00'), to_decimal(rec.amount)))
    for cr in credits:
        rows.append((cr.credit_date, cr.credit_no, 'Credit Note', Decimal('0.00'), to_decimal(cr.total_amount)))
    rows = sorted(rows, key=lambda x: (x[0], x[1]))

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = draw_common_header(pdf, 'CUSTOMER STATEMENT', f'ST-{customer.id:04d}', date.today())
    y = height - 55 * mm
    pdf.drawString(18 * mm, y, f'Customer: {customer.name}')
    y -= 8 * mm

    headers_x = [18 * mm, 45 * mm, 75 * mm, 115 * mm, 145 * mm, 175 * mm]
    headers = ['Date', 'Doc No', 'Type', 'Debit', 'Credit', 'Balance']
    pdf.setFont('Helvetica-Bold', 9)
    for x, h in zip(headers_x, headers):
        pdf.drawString(x, y, h)
    y -= 4 * mm
    pdf.line(18 * mm, y, width - 18 * mm, y)
    y -= 6 * mm

    pdf.setFont('Helvetica', 9)
    for row in rows:
        bal += row[3] - row[4]
        if y < 20 * mm:
            pdf.showPage()
            width, height = draw_common_header(pdf, 'CUSTOMER STATEMENT', f'ST-{customer.id:04d}', date.today())
            y = height - 35 * mm

        pdf.drawString(headers_x[0], y, row[0].strftime('%d-%m-%Y'))
        pdf.drawString(headers_x[1], y, row[1])
        pdf.drawString(headers_x[2], y, row[2])
        pdf.drawRightString(headers_x[4] - 2 * mm, y, money(row[3]))
        pdf.drawRightString(headers_x[5] - 2 * mm, y, money(row[4]))
        pdf.drawRightString(width - 18 * mm, y, money(bal))
        y -= 7 * mm

    pdf.drawString(18 * mm, 15 * mm, COMPANY['footer'])
    pdf.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'statement-{customer.id}.pdf',
        mimetype='application/pdf',
    )


with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('admin123')))
        db.session.commit()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
