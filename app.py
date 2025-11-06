from flask import Flask, render_template
from database import init_db
from face_recognition_system import face_system

# Import all blueprints
from routes.dashboard import dashboard_bp
from routes.register_student import register_student_bp
from routes.view_students import view_students_bp
from routes.take_attendance import take_attendance_bp
from routes.add_subject import add_subject_bp
from routes.view_attendance import view_attendance_bp
from routes.student_portal import student_portal_bp

app = Flask(__name__)
app.secret_key = 'smart-attendance-secret-key-2024'

# Register all blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(register_student_bp)
app.register_blueprint(view_students_bp)
app.register_blueprint(take_attendance_bp)
app.register_blueprint(add_subject_bp)
app.register_blueprint(view_attendance_bp)
app.register_blueprint(student_portal_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print("🚀 Starting Smart Attendance System...")
    print("📊 Loading dashboard charts...")
    print("🎓 Initializing student portal...")
    print("📸 Starting face recognition system...")
    init_db()
    print("✅ Database initialized!")
    print("👤 Face recognition system loaded!")
    print("📍 Web application ready!")
    print("🌐 Server running at: http://127.0.0.1:5000")
    print("\n📋 Available Routes:")
    print("   • /                         - Homepage")
    print("   • /dashboard                - Dashboard with charts")
    print("   • /register_student         - Register new student")
    print("   • /view_students            - View all students")
    print("   • /take_attendance          - Take attendance with photos")
    print("   • /view_attendance          - View attendance records")
    print("   • /add_subject              - Add new subject")
    print("   • /student_portal           - Student portal (NEW!)")
    print("   • /attendance_data          - Chart data API")
    print("   • /update_attendance_record - Manual correction API")
    print("\n🎯 System Features:")
    print("   • Face Recognition Attendance")
    print("   • Manual Attendance Correction")
    print("   • Student Portal (NEW!)")
    print("   • Interactive Charts & Analytics")
    print("   • Student Management")
    print("   • Subject Management")
    print("\n🎓 Student Portal Features:")
    print("   • Students can check their own attendance")
    print("   • View attendance by date and subject")
    print("   • See overall attendance percentage")
    print("   • No password required - just enrollment number")
    
    app.run(debug=True, host='0.0.0.0', port=5000)