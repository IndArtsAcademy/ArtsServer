from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import psycopg2
import os

app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# PostgreSQL Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)

# Create Table for Students
def init_db():
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                guardian_name TEXT NOT NULL,
                guardian_phone TEXT NOT NULL,
                student_phone TEXT,
                dob DATE NOT NULL,
                address TEXT NOT NULL,
                class TEXT NOT NULL,
                subjects TEXT,
                photo_path TEXT
            )
        """)
        conn.commit()

init_db()

# Utility function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route: Home Page
@app.route('/')
def home():
    return "<h1>Welcome to the Admission Server</h1><p>Use the API to submit or manage admissions.</p>"

# Route: Submit Admission
@app.route('/submit', methods=['POST'])
def submit_admission():
    try:
        # Get form data
        name = request.form['name']
        guardian_name = request.form['guardian-name']
        guardian_phone = request.form['guardian-phone']
        student_phone = request.form.get('student-phone', '')
        dob = request.form['dob']
        address = request.form['address']
        class_name = request.form['class']
        subjects = ", ".join(request.form.getlist('subjects'))

        # Handle photo upload
        photo = request.files.get('photo')
        photo_path = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)

        # Save to database
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO students (name, guardian_name, guardian_phone, student_phone, dob, address, class, subjects, photo_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, guardian_name, guardian_phone, student_phone, dob, address, class_name, subjects, photo_path))
            conn.commit()

        return jsonify({"message": "Admission submitted successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route: Admin View (List All Students)
@app.route('/admin', methods=['GET'])
def admin_view():
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM students")
            students = cursor.fetchall()
        
        # Convert student data to JSON
        student_list = [
            {
                "id": row[0],
                "name": row[1],
                "guardian_name": row[2],
                "guardian_phone": row[3],
                "student_phone": row[4],
                "dob": row[5],
                "address": row[6],
                "class": row[7],
                "subjects": row[8],
                "photo_path": row[9]
            }
            for row in students
        ]

        return jsonify({"students": student_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use Render's PORT or default to 5000
    app.run(host='0.0.0.0', port=port)
