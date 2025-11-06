from flask import Blueprint, render_template, jsonify
from datetime import datetime
from database import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    stats = {
        'total_students': 0,
        'students_with_faces': 0,
        'total_subjects': 0,
        'today_attendance': 0
    }
    
    if conn:
        cursor = conn.cursor()
        try:
            # Total students
            cursor.execute('SELECT COUNT(*) as count FROM students')
            stats['total_students'] = cursor.fetchone()['count']
            
            # Students with face data
            cursor.execute('SELECT COUNT(*) as count FROM face_encodings')
            stats['students_with_faces'] = cursor.fetchone()['count']
            
            # Total subjects
            cursor.execute('SELECT COUNT(*) as count FROM subjects')
            stats['total_subjects'] = cursor.fetchone()['count']
            
            # Today's attendance
            cursor.execute('''
                SELECT COUNT(*) as count FROM attendance_records 
                WHERE DATE(recognition_time) = CURDATE() AND status = "present"
            ''')
            stats['today_attendance'] = cursor.fetchone()['count']
            
        except Exception as e:
            print(f"Dashboard stats error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('dashboard.html', stats=stats, now=datetime.now())

@dashboard_bp.route('/attendance_data')
def attendance_data():
    """API endpoint for chart data"""
    conn = get_db_connection()
    chart_data = {
        'weekly_trend': [],
        'subject_wise': [],
        'daily_attendance': []
    }
    
    if conn:
        cursor = conn.cursor()
        try:
            # Weekly trend data (last 7 days)
            cursor.execute('''
                SELECT DATE(session_date) as date, 
                       ROUND(AVG((present_count / NULLIF(total_students, 0)) * 100), 1) as attendance_percent
                FROM attendance_sessions 
                WHERE session_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(session_date)
                ORDER BY date
            ''')
            weekly_data = cursor.fetchall()
            
            # Fill missing days with 0
            import datetime
            for i in range(7):
                date = datetime.date.today() - datetime.timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                if not any(d['date'].strftime('%Y-%m-%d') == date_str for d in weekly_data):
                    weekly_data.append({'date': date, 'attendance_percent': 0})
            
            chart_data['weekly_trend'] = sorted(weekly_data, key=lambda x: x['date'])
            
            # Subject-wise attendance
            cursor.execute('''
                SELECT s.subject_name,
                       ROUND(AVG((a.present_count / NULLIF(a.total_students, 0)) * 100), 1) as avg_attendance
                FROM attendance_sessions a
                JOIN subjects s ON a.subject_id = s.subject_id
                GROUP BY s.subject_id, s.subject_name
                ORDER BY avg_attendance DESC
                LIMIT 6
            ''')
            chart_data['subject_wise'] = cursor.fetchall()
            
            # Today's attendance by section
            cursor.execute('''
                SELECT section, 
                       ROUND((present_count / NULLIF(total_students, 0)) * 100, 1) as attendance_percent,
                       present_count,
                       total_students
                FROM attendance_sessions 
                WHERE session_date = CURDATE()
                ORDER BY section
            ''')
            daily_data = cursor.fetchall()
            
            # Ensure all sections are represented
            sections = ['A', 'B', 'C']
            for section in sections:
                if not any(d['section'] == section for d in daily_data):
                    daily_data.append({
                        'section': section, 
                        'attendance_percent': 0,
                        'present_count': 0,
                        'total_students': 0
                    })
            
            chart_data['daily_attendance'] = sorted(daily_data, key=lambda x: x['section'])
            
        except Exception as e:
            print(f"Chart data error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return jsonify(chart_data)