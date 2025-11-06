from flask import Blueprint, render_template, request, flash, redirect, url_for
from database import get_db_connection, execute_with_retry
from face_recognition_system import face_system

register_student_bp = Blueprint('register_student', __name__)

@register_student_bp.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        try:
            # Form data
            enrollment_no = request.form.get('enrollment_no', '').strip()
            name = request.form.get('name', '').strip()
            roll_no = request.form.get('roll_no', '').strip()
            phone = request.form.get('phone', '').strip()
            parent_phone = request.form.get('parent_phone', '').strip()
            email = request.form.get('email', '').strip()
            course = request.form.get('course', '').strip()
            semester = request.form.get('semester', '').strip()
            section = request.form.get('section', '').strip()
            
            # Multiple photos from automatic capture
            photo_data_1 = request.form.get('photo_data_1', '')
            photo_data_2 = request.form.get('photo_data_2', '')
            photo_data_3 = request.form.get('photo_data_3', '')
            photo_data_4 = request.form.get('photo_data_4', '')
            
            print(f"📝 Registering student: {enrollment_no} - {name}")
            
            # Validation
            if not enrollment_no or not name or not section:
                flash('❌ Enrollment number, name and section are required', 'error')
                return render_template('register_student.html')
            
            # Collect all valid photos
            photo_data_list = [photo_data_1, photo_data_2, photo_data_3, photo_data_4]
            valid_photos = [photo for photo in photo_data_list if photo]
            
            if len(valid_photos) == 0:
                flash('❌ Please capture face photos using automatic capture', 'error')
                return render_template('register_student.html')
            
            print(f"📸 Processing {len(valid_photos)} face photos for {enrollment_no}")
            
            # Extract face encodings from multiple photos
            all_face_encodings = []
            successful_encodings = 0
            
            for i, photo_data in enumerate(valid_photos):
                face_encoding, face_message = face_system.extract_face_encoding(photo_data)
                
                if face_encoding is not None:
                    all_face_encodings.append(face_encoding)
                    successful_encodings += 1
                    print(f"✅ Photo {i+1}: Face encoding extracted successfully")
                else:
                    print(f"⚠️ Photo {i+1}: {face_message}")
            
            if len(all_face_encodings) == 0:
                flash('❌ Could not extract face features from any photo', 'error')
                return render_template('register_student.html')
            
            # Calculate average face encoding from all successful photos
            avg_face_encoding = sum(all_face_encodings) / len(all_face_encodings)
            
            # Save student to database
            query = '''
                INSERT INTO students 
                (enrollment_no, name, roll_no, phone, parent_phone, email, course, semester, section)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            params = (enrollment_no, name, roll_no, phone, parent_phone, email, course, semester, section)
            
            cursor, db_message = execute_with_retry(query, params)
            
            if not cursor:
                flash(f'❌ Database error: {db_message}', 'error')
                return render_template('register_student.html')
            
            # Save average face encoding
            success, encoding_message = face_system.save_face_encoding(enrollment_no, avg_face_encoding)
            
            if success:
                # Reload known faces
                face_system.load_known_faces()
                flash(f'✅ Student registered successfully with {successful_encodings} face samples!', 'success')
                print(f"🎉 Student {enrollment_no} registered with {successful_encodings} face encodings!")
            else:
                flash(f'⚠️ Student registered but face encoding failed: {encoding_message}', 'warning')
            
            return redirect(url_for('view_students.view_students'))
            
        except Exception as e:
            flash(f'❌ Registration error: {str(e)}', 'error')
            print(f"🚨 REGISTRATION ERROR: {e}")
            return render_template('register_student.html')
    
    return render_template('register_student.html')