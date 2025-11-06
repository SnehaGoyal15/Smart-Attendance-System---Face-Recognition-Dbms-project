from flask import Blueprint, request, jsonify
from database import get_db_connection

correct_attendance_bp = Blueprint('correct_attendance', __name__)

@correct_attendance_bp.route('/update_attendance_record', methods=['POST'])
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