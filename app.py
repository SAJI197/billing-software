import streamlit as st
import pandas as pd
from datetime import date
import os

DATA_DIR = 'data'
CUSTOMERS_FILE = os.path.join(DATA_DIR, 'customers.csv')
INVOICES_FILE = os.path.join(DATA_DIR, 'invoices.csv')
PAYMENTS_FILE = os.path.join(DATA_DIR, 'payments.csv')

os.makedirs(DATA_DIR, exist_ok=True)


def load_csv(path, columns):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)


def save_csv(df, path):
    df.to_csv(path, index=False)


customers = load_csv(CUSTOMERS_FILE, ['customer_name', 'phone', 'address'])
invoices = load_csv(INVOICES_FILE, ['invoice_no', 'invoice_date', 'customer_name', 'description', 'amount', 'tax_percent', 'tax_amount', 'total_amount', 'status'])
payments = load_csv(PAYMENTS_FILE, ['payment_date', 'customer_name', 'invoice_no', 'amount_received', 'notes'])

st.set_page_config(page_title='Simple Billing Software', layout='wide')
st.title('Simple Billing Software')
st.caption('Invoice • Ledger • Payments • Reports')

menu = st.sidebar.radio('Choose Section', ['Dashboard', 'Add Customer', 'Create Invoice', 'Record Payment', 'Customer Ledger', 'Reports'])

if menu == 'Dashboard':
    total_sales = pd.to_numeric(invoices.get('total_amount', pd.Series(dtype=float)), errors='coerce').fillna(0).sum() if not invoices.empty else 0
    total_received = pd.to_numeric(payments.get('amount_received', pd.Series(dtype=float)), errors='coerce').fillna(0).sum() if not payments.empty else 0
    balance = total_sales - total_received

    c1, c2, c3 = st.columns(3)
    c1.metric('Total Sales', f'{total_sales:,.2f}')
    c2.metric('Total Received', f'{total_received:,.2f}')
    c3.metric('Balance Outstanding', f'{balance:,.2f}')

    st.subheader('Recent Invoices')
    st.dataframe(invoices.tail(10), use_container_width=True)

    st.subheader('Recent Payments')
    st.dataframe(payments.tail(10), use_container_width=True)

elif menu == 'Add Customer':
    st.subheader('Add Customer')
    with st.form('customer_form'):
        customer_name = st.text_input('Customer Name')
        phone = st.text_input('Phone')
        address = st.text_area('Address')
        submitted = st.form_submit_button('Save Customer')

    if submitted:
        if customer_name.strip() == '':
            st.error('Customer name is required.')
        else:
            new_row = pd.DataFrame([{
                'customer_name': customer_name.strip(),
                'phone': phone.strip(),
                'address': address.strip()
            }])
            customers = pd.concat([customers, new_row], ignore_index=True)
            save_csv(customers, CUSTOMERS_FILE)
            st.success('Customer saved successfully.')

    st.subheader('Customer List')
    st.dataframe(customers, use_container_width=True)

elif menu == 'Create Invoice':
    st.subheader('Create Invoice')
    customer_options = customers['customer_name'].dropna().tolist() if not customers.empty else []

    with st.form('invoice_form'):
        invoice_no = st.text_input('Invoice Number', value=f'INV-{len(invoices)+1:04d}')
        invoice_date = st.date_input('Invoice Date', value=date.today())
        customer_name = st.selectbox('Customer Name', options=customer_options) if customer_options else st.text_input('Customer Name')
        description = st.text_area('Description / Service Details')
        amount = st.number_input('Amount', min_value=0.0, step=1.0)
        tax_percent = st.number_input('Tax %', min_value=0.0, step=1.0, value=5.0)
        submitted = st.form_submit_button('Save Invoice')

    if submitted:
        tax_amount = amount * tax_percent / 100
        total_amount = amount + tax_amount
        new_row = pd.DataFrame([{
            'invoice_no': invoice_no,
            'invoice_date': invoice_date,
            'customer_name': customer_name,
            'description': description,
            'amount': amount,
            'tax_percent': tax_percent,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'status': 'Unpaid'
        }])
        invoices = pd.concat([invoices, new_row], ignore_index=True)
        save_csv(invoices, INVOICES_FILE)
        st.success(f'Invoice saved. Total Invoice Amount: {total_amount:,.2f}')

    st.subheader('Invoice List')
    st.dataframe(invoices, use_container_width=True)

elif menu == 'Record Payment':
    st.subheader('Record Payment')
    invoice_options = invoices['invoice_no'].dropna().tolist() if not invoices.empty else []
    customer_options = customers['customer_name'].dropna().tolist() if not customers.empty else []

    with st.form('payment_form'):
        payment_date = st.date_input('Payment Date', value=date.today())
        customer_name = st.selectbox('Customer Name', options=customer_options) if customer_options else st.text_input('Customer Name')
        invoice_no = st.selectbox('Invoice Number', options=invoice_options) if invoice_options else st.text_input('Invoice Number')
        amount_received = st.number_input('Amount Received', min_value=0.0, step=1.0)
        notes = st.text_input('Notes')
        submitted = st.form_submit_button('Save Payment')

    if submitted:
        new_row = pd.DataFrame([{
            'payment_date': payment_date,
            'customer_name': customer_name,
            'invoice_no': invoice_no,
            'amount_received': amount_received,
            'notes': notes
        }])
        payments = pd.concat([payments, new_row], ignore_index=True)
        save_csv(payments, PAYMENTS_FILE)

        if not invoices.empty and invoice_no in invoices['invoice_no'].values:
            inv_total = float(invoices.loc[invoices['invoice_no'] == invoice_no, 'total_amount'].iloc[0])
            paid_total = pd.to_numeric(payments.loc[payments['invoice_no'] == invoice_no, 'amount_received'], errors='coerce').fillna(0).sum()
            status = 'Paid' if paid_total >= inv_total else 'Partly Paid'
            invoices.loc[invoices['invoice_no'] == invoice_no, 'status'] = status
            save_csv(invoices, INVOICES_FILE)

        st.success('Payment recorded successfully.')

    st.subheader('Payment List')
    st.dataframe(payments, use_container_width=True)

elif menu == 'Customer Ledger':
    st.subheader('Customer Ledger')
    customer_options = customers['customer_name'].dropna().tolist() if not customers.empty else []
    selected_customer = st.selectbox('Select Customer', options=customer_options) if customer_options else st.text_input('Customer Name')

    if selected_customer:
        cust_invoices = invoices[invoices['customer_name'] == selected_customer].copy() if not invoices.empty else pd.DataFrame()
        cust_payments = payments[payments['customer_name'] == selected_customer].copy() if not payments.empty else pd.DataFrame()

        st.write('### Invoices')
        st.dataframe(cust_invoices, use_container_width=True)

        st.write('### Payments')
        st.dataframe(cust_payments, use_container_width=True)

        total_invoice = pd.to_numeric(cust_invoices.get('total_amount', pd.Series(dtype=float)), errors='coerce').fillna(0).sum() if not cust_invoices.empty else 0
        total_payment = pd.to_numeric(cust_payments.get('amount_received', pd.Series(dtype=float)), errors='coerce').fillna(0).sum() if not cust_payments.empty else 0
        balance = total_invoice - total_payment

        c1, c2, c3 = st.columns(3)
        c1.metric('Total Invoiced', f'{total_invoice:,.2f}')
        c2.metric('Total Received', f'{total_payment:,.2f}')
        c3.metric('Balance', f'{balance:,.2f}')

elif menu == 'Reports':
    st.subheader('Reports')
    st.write('### Full Invoice Report')
    st.dataframe(invoices, use_container_width=True)

    st.write('### Full Payment Report')
    st.dataframe(payments, use_container_width=True)

    if not invoices.empty:
        csv = invoices.to_csv(index=False).encode('utf-8')
        st.download_button('Download Invoice Report CSV', data=csv, file_name='invoice_report.csv', mime='text/csv')

    if not payments.empty:
        csv2 = payments.to_csv(index=False).encode('utf-8')
        st.download_button('Download Payment Report CSV', data=csv2, file_name='payment_report.csv', mime='text/csv')
