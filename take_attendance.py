from flask import Blueprint, render_template, request, flash, redirect, url_for
from datetime import datetime
import base64
from database import get_db_connection, execute_with_retry
from face_recognition_system import face_system

take_attendance_bp = Blueprint('take_attendance', __name__)

@take_attendance_bp.route('/take_attendance', methods=['GET', 'POST'])
def take_attendance():
    # Get subjects for dropdown
    conn = get_db_connection()
    subjects = []
    
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM subjects')
            subjects = cursor.fetchall()
        except Exception as e:
            print(f"Subjects error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    if request.method == 'POST':
        try:
            subject_id = request.form.get('subject_id')
            section = request.form.get('section')
            
            if not subject_id or not section:
                flash('❌ Please select subject and section', 'error')
                return redirect(url_for('take_attendance.take_attendance'))
            
            # Get uploaded photos
            uploaded_photos = request.files.getlist('group_photos')
            
            if not uploaded_photos or len(uploaded_photos) == 0:
                flash('❌ Please upload at least one class photo', 'error')
                return redirect(url_for('take_attendance.take_attendance'))
            
            print(f"📸 Processing {len(uploaded_photos)} uploaded photos...")
            
            all_recognized_students = []
            total_faces_detected = 0
            
            # Process each uploaded photo
            for i, photo in enumerate(uploaded_photos):
                if photo.filename == '':
                    continue
                    
                # Convert uploaded file to base64
                photo_data = base64.b64encode(photo.read()).decode('utf-8')
                photo_data = f"data:image/jpeg;base64,{photo_data}"
                
                # Face recognition from this photo
                recognized_students, faces_in_photo = face_system.recognize_faces_in_group_photo(photo_data)
                
                print(f"📊 Photo {i+1}: {len(recognized_students)} recognized out of {faces_in_photo} faces")
                
                # Add to overall results (avoid duplicates)
                for student in recognized_students:
                    if student['enrollment_no'] not in [s['enrollment_no'] for s in all_recognized_students]:
                        all_recognized_students.append(student)
                
                total_faces_detected += faces_in_photo
            
            print(f"🎯 Total recognition: {len(all_recognized_students)} unique students from {total_faces_detected} faces")
            
            # Create attendance session
            conn = get_db_connection()
            if not conn:
                flash('❌ Database connection failed', 'error')
                return redirect(url_for('take_attendance.take_attendance'))
            
            cursor = conn.cursor()
            
            # Create attendance session
            cursor.execute('''
                INSERT INTO attendance_sessions 
                (subject_id, section, session_date, session_time, total_students, present_count)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                subject_id, section, 
                datetime.now().date(), datetime.now().time(),
                total_faces_detected, len(all_recognized_students)
            ))
            
            session_id = cursor.lastrowid
            
            # Get all students from this section
            cursor.execute('SELECT enrollment_no, name FROM students WHERE section = %s', (section,))
            all_students = cursor.fetchall()
            
            # Create attendance records
            recognized_enrollments = [s['enrollment_no'] for s in all_recognized_students]
            
            for student in all_students:
                status = 'present' if student['enrollment_no'] in recognized_enrollments else 'absent'
                
                # Find confidence for recognized students
                confidence = None
                if status == 'present':
                    for recognized in all_recognized_students:
                        if recognized['enrollment_no'] == student['enrollment_no']:
                            confidence = recognized['confidence']
                            break
                
                cursor.execute('''
                    INSERT INTO attendance_records 
                    (session_id, enrollment_no, status, confidence_score)
                    VALUES (%s, %s, %s, %s)
                ''', (session_id, student['enrollment_no'], status, confidence))
            
            conn.commit()
            
            flash(
                f'✅ Attendance taken successfully! '
                f'Recognized {len(all_recognized_students)}/{total_faces_detected} students in section {section} '
                f'from {len(uploaded_photos)} photos.',
                'success'
            )
            
            return redirect(url_for('take_attendance.take_attendance'))
            
        except Exception as e:
            flash(f'❌ Attendance error: {str(e)}', 'error')
            print(f"🚨 ATTENDANCE ERROR: {e}")
        
        return redirect(url_for('take_attendance.take_attendance'))
    
    return render_template('take_attendance.html', subjects=subjects)