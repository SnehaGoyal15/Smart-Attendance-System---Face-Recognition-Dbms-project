from flask import Blueprint, render_template, request, flash, redirect, url_for
from database import get_db_connection

add_subject_bp = Blueprint('add_subject', __name__)

@add_subject_bp.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        subject_code = request.form.get('subject_code', '').strip()
        subject_name = request.form.get('subject_name', '').strip()
        course = request.form.get('course', '').strip()
        semester = request.form.get('semester', '').strip()
        section = request.form.get('section', '').strip()
        
        if subject_code and subject_name and section:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO subjects (subject_code, subject_name, course, semester, section)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (subject_code, subject_name, course, semester, section))
                    
                    conn.commit()
                    flash('✅ Subject added successfully!', 'success')
                    
                except Exception as e:
                    flash(f'❌ Error adding subject: {str(e)}', 'error')
                finally:
                    cursor.close()
                    conn.close()
        
        return redirect(url_for('add_subject.add_subject'))
    
    return render_template('add_subject.html')