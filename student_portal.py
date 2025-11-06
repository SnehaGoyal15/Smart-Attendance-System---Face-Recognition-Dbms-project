from flask import Blueprint, render_template, request, flash, jsonify
from database import get_db_connection

student_portal_bp = Blueprint('student_portal', __name__)

@student_portal_bp.route('/student_portal', methods=['GET', 'POST'])
def student_portal():
    attendance_data = []
    student_info = None
    enrollment_no = ""
    
    if request.method == 'POST':
        enrollment_no = request.form.get('enrollment_no', '').strip()
        
        if not enrollment_no:
            flash('❌ Please enter your enrollment number', 'error')
            return render_template('student_portal.html', 
                                 attendance_data=attendance_data, 
                                 student_info=student_info,
                                 enrollment_no=enrollment_no)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                # Verify student exists
                cursor.execute('''
                    SELECT enrollment_no, name, roll_no, section, course, semester
                    FROM students 
                    WHERE enrollment_no = %s
                ''', (enrollment_no,))
                
                student_result = cursor.fetchone()
                
                if not student_result:
                    flash('❌ Student not found with this enrollment number', 'error')
                    return render_template('student_portal.html', 
                                         attendance_data=attendance_data, 
                                         student_info=student_info,
                                         enrollment_no=enrollment_no)
                
                student_info = student_result
                
                # Get attendance records for this student - FIXED QUERY
                cursor.execute('''
                    SELECT 
                        ar.record_id,
                        ar.session_id,
                        sec.session_date,
                        sub.subject_code,
                        sub.subject_name,
                        ar.status,
                        ar.confidence_score,
                        ar.recognition_time,
                        sec.section,
                        sec.present_count,
                        sec.total_students,
                        COALESCE(ROUND((sec.present_count / NULLIF(sec.total_students, 0)) * 100, 1), 0) as class_attendance
                    FROM attendance_records ar
                    JOIN attendance_sessions sec ON ar.session_id = sec.session_id
                    JOIN subjects sub ON sec.subject_id = sub.subject_id
                    WHERE ar.enrollment_no = %s
                    ORDER BY sec.session_date DESC, sub.subject_name
                ''', (enrollment_no,))
                
                attendance_data = cursor.fetchall()
                
                if not attendance_data:
                    flash('ℹ️ No attendance records found for this student', 'info')
                else:
                    flash(f'✅ Found {len(attendance_data)} attendance records', 'success')
                
            except Exception as e:
                print(f"Student portal error: {e}")
                flash('❌ Error fetching attendance data', 'error')
            finally:
                cursor.close()
                conn.close()
    
    return render_template('student_portal.html',
                         attendance_data=attendance_data,
                         student_info=student_info,
                         enrollment_no=enrollment_no)

@student_portal_bp.route('/student_attendance_data')
def student_attendance_data():
    """API for student attendance chart"""
    enrollment_no = request.args.get('enrollment_no')
    
    if not enrollment_no:
        return {"error": "Enrollment number required"}
    
    conn = get_db_connection()
    chart_data = {
        'subject_wise': [],
        'daily_attendance': [],
        'overall_stats': {}
    }
    
    if conn:
        cursor = conn.cursor()
        try:
            # Subject-wise attendance
            cursor.execute('''
                SELECT 
                    sub.subject_name,
                    COUNT(*) as total_classes,
                    SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) as present_classes,
                    COALESCE(ROUND((SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 1), 0) as attendance_percent
                FROM attendance_records ar
                JOIN attendance_sessions sec ON ar.session_id = sec.session_id
                JOIN subjects sub ON sec.subject_id = sub.subject_id
                WHERE ar.enrollment_no = %s
                GROUP BY sub.subject_id, sub.subject_name
                ORDER BY attendance_percent DESC
            ''', (enrollment_no,))
            
            chart_data['subject_wise'] = cursor.fetchall()
            
            # Recent attendance (last 30 days)
            cursor.execute('''
                SELECT 
                    sec.session_date,
                    COUNT(*) as total_classes,
                    SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) as present_classes,
                    COALESCE(ROUND((SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 1), 0) as daily_percent
                FROM attendance_records ar
                JOIN attendance_sessions sec ON ar.session_id = sec.session_id
                WHERE ar.enrollment_no = %s AND sec.session_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY sec.session_date
                ORDER BY sec.session_date DESC
                LIMIT 15
            ''', (enrollment_no,))
            
            chart_data['daily_attendance'] = cursor.fetchall()
            
            # Overall statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_classes,
                    SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) as present_classes,
                    COALESCE(ROUND((SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 1), 0) as overall_percent
                FROM attendance_records ar
                WHERE ar.enrollment_no = %s
            ''', (enrollment_no,))
            
            overall_stats = cursor.fetchone()
            if overall_stats:
                chart_data['overall_stats'] = overall_stats
            
        except Exception as e:
            print(f"Student chart data error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return chart_data

# Test route to see available students (optional - remove in production)
@student_portal_bp.route('/test_students')
def test_students():
    """Test route to see available students"""
    conn = get_db_connection()
    students = []
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT enrollment_no, name FROM students LIMIT 10')
            students = cursor.fetchall()
        except Exception as e:
            print(f"Test error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    result = "<h1>Available Students:</h1><ul>"
    for student in students:
        result += f"<li>{student['enrollment_no']} - {student['name']}</li>"
    result += "</ul>"
    return result