from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db_connection

students_bp = Blueprint('students', __name__)

# Update Student Route
@students_bp.route('/update_student', methods=['POST'])
def update_student():
    try:
        # Get form data
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
                # Update student in database
                cursor.execute('''
                    UPDATE students 
                    SET roll_no = %s, name = %s, email = %s, phone = %s, section = %s
                    WHERE enrollment_no = %s
                ''', (roll_no, name, email, phone, section, enrollment_no))
                
                conn.commit()
                flash('✅ Student updated successfully!', 'success')
                print(f"📝 Student updated: {enrollment_no} - {name}")
                
            except Exception as e:
                conn.rollback()
                flash('❌ Error updating student!', 'error')
                print(f"Update student error: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            flash('❌ Database connection error!', 'error')
            
    except Exception as e:
        flash('❌ Form data error!', 'error')
        print(f"Form error: {e}")
    
    return redirect(url_for('view_students.view_students'))

# Delete Student Route  
@students_bp.route('/delete_student', methods=['GET'])
def delete_student():
    try:
        enrollment_no = request.args.get('enrollment_no')
        
        if enrollment_no:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    # Delete student from database
                    cursor.execute('DELETE FROM students WHERE enrollment_no = %s', (enrollment_no,))
                    conn.commit()
                    flash('✅ Student deleted successfully!', 'success')
                    print(f"🗑️ Student deleted: {enrollment_no}")
                    
                except Exception as e:
                    conn.rollback()
                    flash('❌ Error deleting student!', 'error')
                    print(f"Delete student error: {e}")
                finally:
                    cursor.close()
                    conn.close()
            else:
                flash('❌ Database connection error!', 'error')
        else:
            flash('❌ No enrollment number provided!', 'error')
            
    except Exception as e:
        flash('❌ Error processing request!', 'error')
        print(f"Delete request error: {e}")
    
    return redirect(url_for('view_students.view_students'))