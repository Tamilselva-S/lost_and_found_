from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
from datetime import datetime
import yagmail
from fpdf import FPDF  # Add this line

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['REPORT_FOLDER'] = 'static/reports'

# MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="selva2005",  # Update if needed
    database="lost_found_db"
)
cursor = conn.cursor()

# Gmail Setup
sender_email = "kkstamil0312@gmail.com"
app_password = "qjgwwzyzqtjfpkum"  # App password

recipients = [
    "23cse171@act.edu.in",
    "23cse154@act.edu.in",  # Sathya
    #"23cse144@act.edu.in",  # R
    #"kalarani.cse@act.edu.in" # Kalarani Mam
]

# 📄 Generate PDF Report
def generate_pdf(name, description, location, contact, item_type, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Lost & Found Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Type: {item_type}", ln=True)
    pdf.cell(200, 10, txt=f"Name: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Description: {description}", ln=True)
    pdf.cell(200, 10, txt=f"Location: {location}", ln=True)
    pdf.cell(200, 10, txt=f"Contact: {contact}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)

    # Add a line break
    pdf.ln(10)

    # Add the image
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(image_path):
        pdf.cell(200, 10, txt="Attached Image:", ln=True)
        pdf.image(image_path, w=100)  # Adjust width as needed
    else:
        pdf.cell(200, 10, txt="Image not found.", ln=True)

    # Save report
    report_path = os.path.join(app.config['REPORT_FOLDER'], "report.pdf")
    pdf.output(report_path)
    return report_path


# 📧 Send Email with PDF
def send_notification_email(name, description, location, contact, item_type, image_filename):
    body = f"""
Hello,

A new item has been reported in the Lost & Found portal.

Type: {item_type}
Name: {name}
Description: {description}
Location: {location}
Contact: {contact}

Please check the attached report for more details.

Thanks,
Lost & Found System
"""
    # Generate PDF first
    report_pdf = generate_pdf(name, description, location, contact, item_type, image_filename)

    yag = yagmail.SMTP(sender_email, app_password)
    yag.send(
        to=recipients,
        subject=f"Lost & Found Notification - {item_type}",
        contents=body,
        attachments=[report_pdf]
    )

# 🏠 Home Page
@app.route('/')
def index():
    return render_template('index.html')

# 🧍 Lost Form
@app.route('/lost', methods=['GET', 'POST'])
def lost():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        location = request.form['location']
        contact = request.form['contact']
        image = request.files['image']
        filename = image.filename
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cursor.execute(
            "INSERT INTO items (type, name, description, location, contact, image, date) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            ('Lost', name, description, location, contact, filename, datetime.now())
        )
        conn.commit()

        send_notification_email(name, description, location, contact, "Lost", filename)
        return redirect(url_for('index'))

    return render_template('lost.html')

# 🧳 Found Form
@app.route('/found', methods=['GET', 'POST'])
def found():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        location = request.form['location']
        contact = request.form['contact']
        image = request.files['image']
        filename = image.filename
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cursor.execute(
            "INSERT INTO items (type, name, description, location, contact, image, date) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            ('Found', name, description, location, contact, filename, datetime.now())
        )
        conn.commit()

        send_notification_email(name, description, location, contact, "Found", filename)
        return redirect(url_for('index'))

    return render_template('found.html')

# 👁️ View All
@app.route('/view')
def view_items():
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    return render_template('view_items.html', items=items)

# ❌ Delete
@app.route('/delete/<int:id>', methods=['POST'])
def delete_item(id):
    cursor.execute("SELECT image FROM items WHERE id = %s", (id,))
    result = cursor.fetchone()

    if result:
        image_filename = result[0]
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)

        cursor.execute("DELETE FROM items WHERE id = %s", (id,))
        conn.commit()

    return redirect(url_for('view_items'))

if __name__ == '__main__':
    # Make sure folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

    app.run(debug=True)
