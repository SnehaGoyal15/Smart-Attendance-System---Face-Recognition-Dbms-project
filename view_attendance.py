from flask import Blueprint, render_template, request, jsonify
from database import get_db_connection

view_attendance_bp = Blueprint('view_attendance', __name__)

@view_attendance_bp.route('/view_attendance')
def view_attendance():
    # Get filter parameters
    subject_id = request.args.get('subject_id', '')
    section = request.args.get('section', '')
    date = request.args.get('date', '')
    
    conn = get_db_connection()
    attendance_data = []
    subjects = []
    sessions = []
    
    if conn:
        cursor = conn.cursor()
        try:
            # Get all subjects for filter
            cursor.execute('SELECT * FROM subjects')
            subjects = cursor.fetchall()
            
            # Build query for attendance sessions
            query = '''
                SELECT 
                    s.session_id,
                    s.session_date,
                    s.session_time,
                    s.section,
                    s.total_students,
                    s.present_count,
                    sub.subject_code,
                    sub.subject_name,
                    COALESCE(ROUND((s.present_count / NULLIF(s.total_students, 0)) * 100, 1), 0) as attendance_percentage
                FROM attendance_sessions s
                JOIN subjects sub ON s.subject_id = sub.subject_id
                WHERE 1=1
            '''
            params = []
            
            if subject_id:
                query += ' AND s.subject_id = %s'
                params.append(subject_id)
            
            if section:
                query += ' AND s.section = %s'
                params.append(section)
            
            if date:
                query += ' AND s.session_date = %s'
                params.append(date)
            
            query += ' ORDER BY s.session_date DESC, s.session_time DESC'
            
            cursor.execute(query, params)
            sessions = cursor.fetchall()
            
            # Get detailed attendance records if session_id provided
            session_id = request.args.get('session_id', '')
            if session_id:
                cursor.execute('''
                    SELECT 
                        ar.record_id,
                        ar.enrollment_no,
                        s.name,
                        ar.status,
                        ar.confidence_score,
                        ar.recognition_time
                    FROM attendance_records ar
                    JOIN students s ON ar.enrollment_no = s.enrollment_no
                    WHERE ar.session_id = %s
                    ORDER BY s.name
                ''', (session_id,))
                attendance_data = cursor.fetchall()
            
        except Exception as e:
            print(f"View attendance error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('view_attendance.html', 
                         sessions=sessions,
                         attendance_data=attendance_data,
                         subjects=subjects,
                         filters={
                             'subject_id': subject_id,
                             'section': section,
                             'date': date,
                             'session_id': request.args.get('session_id', '')
                         })

# ADD MANUAL CORRECTION ROUTE HERE
@view_attendance_bp.route('/update_attendance_record', methods=['POST'])
def update_attendance_record():
    """Update individual attendance record"""
    conn = None
    cursor = None
    try:
        record_id = request.form.get('record_id')
        new_status = request.form.get('status')
        
        print(f"📝 Updating record {record_id} to {new_status}")
        
        if not record_id or not new_status:
            return jsonify({'success': False, 'error': 'Missing record_id or status'})
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'})
        
        cursor = conn.cursor()
        
        # Get session_id first
        cursor.execute('SELECT session_id FROM attendance_records WHERE record_id = %s', (record_id,))
        session_result = cursor.fetchone()
        
        if not session_result:
            return jsonify({'success': False, 'error': 'Record not found'})
        
        session_id = session_result['session_id']
        
        # Update the attendance record
        cursor.execute('''
            UPDATE attendance_records 
            SET status = %s, recognition_time = CURRENT_TIMESTAMP
            WHERE record_id = %s
        ''', (new_status, record_id))
        
        # Update the session counts
        cursor.execute('''
            SELECT COUNT(*) as present_count 
            FROM attendance_records 
            WHERE session_id = %s AND status = 'present'
        ''', (session_id,))
        
        present_count_result = cursor.fetchone()
        present_count = present_count_result['present_count'] if present_count_result else 0
        
        cursor.execute('''
            UPDATE attendance_sessions 
            SET present_count = %s
            WHERE session_id = %s
        ''', (present_count, session_id))
        
        conn.commit()
        
        print(f"✅ Successfully updated record {record_id} to {new_status}")
        return jsonify({'success': True, 'message': 'Attendance updated successfully'})
        
    except Exception as e:
        print(f"❌ Error updating attendance: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()