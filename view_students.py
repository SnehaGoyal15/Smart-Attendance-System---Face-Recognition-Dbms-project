from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db_connection

view_students_bp = Blueprint('view_students', __name__)

@view_students_bp.route('/view_students')
def view_students():
    # Get filter parameters
    section = request.args.get('section', '')
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    students = []
    
    if conn:
        cursor = conn.cursor()
        try:
            # Build query for students with filtering
            query = '''
                SELECT s.*, fe.face_encoding IS NOT NULL as has_face_data 
                FROM students s 
                LEFT JOIN face_encodings fe ON s.enrollment_no = fe.enrollment_no
                WHERE 1=1
            '''
            params = []
            
            if section:
                query += ' AND s.section = %s'
                params.append(section)
            
            if search:
                query += ' AND (s.enrollment_no LIKE %s OR s.roll_no LIKE %s OR s.name LIKE %s OR s.email LIKE %s OR s.phone LIKE %s)'
                search_term = f'%{search}%'
                params.extend([search_term, search_term, search_term, search_term, search_term])
            
            query += ' ORDER BY s.enrollment_no'
            
            cursor.execute(query, params)
            students = cursor.fetchall()
            
            print(f"📊 Loaded {len(students)} students from database")
                
        except Exception as e:
            print(f"View students error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('view_students.html', 
                         students=students,
                         filters={
                             'section': section,
                             'search': search
                         })

# UPDATE STUDENT ROUTE - YEH ADD KARO
@view_students_bp.route('/update_student', methods=['POST'])
def update_student():
    try:
        enrollment_no = request.form['enrollment_no']
        roll_no = request.form.get('roll_no', '')
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        section = request.form['section']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE students 
                    SET roll_no = %s, name = %s, email = %s, phone = %s, section = %s
                    WHERE enrollment_no = %s
                ''', (roll_no, name, email, phone, section, enrollment_no))
                
                conn.commit()
                flash('✅ Student updated successfully!', 'success')
                print(f"📝 Updated: {enrollment_no}")
                
            except Exception as e:
                conn.rollback()
                flash('❌ Error updating student!', 'error')
                print(f"Update error: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            flash('❌ Database connection error!', 'error')
            
    except Exception as e:
        flash('❌ Form data error!', 'error')
        print(f"Form error: {e}")
    
    return redirect(url_for('view_students.view_students'))

# DELETE STUDENT ROUTE - YEH BHI ADD KARO
@view_students_bp.route('/delete_student', methods=['GET'])
def delete_student():
    try:
        enrollment_no = request.args.get('enrollment_no')
        
        if enrollment_no:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('DELETE FROM students WHERE enrollment_no = %s', (enrollment_no,))
                    conn.commit()
                    flash('✅ Student deleted successfully!', 'success')
                    print(f"🗑️ Deleted: {enrollment_no}")
                    
                except Exception as e:
                    conn.rollback()
                    flash('❌ Error deleting student!', 'error')
                    print(f"Delete error: {e}")
                finally:
                    cursor.close()
                    conn.close()
        else:
            flash('❌ No enrollment number provided!', 'error')
            
    except Exception as e:
        flash('❌ Error processing request!', 'error')
        print(f"Delete request error: {e}")
    
    return redirect(url_for('view_students.view_students'))