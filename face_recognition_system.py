import face_recognition
import pickle
import numpy as np
from PIL import Image
import io
import base64
from database import get_db_connection

class FaceRecognitionSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_enrollments = []
        self.known_face_names = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Database se saare face encodings load karo"""
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT s.enrollment_no, s.name, fe.face_encoding 
                    FROM students s 
                    JOIN face_encodings fe ON s.enrollment_no = fe.enrollment_no
                ''')
                students = cursor.fetchall()
                
                self.known_face_encodings = []
                self.known_face_enrollments = []
                self.known_face_names = []
                
                for student in students:
                    try:
                        face_encoding = pickle.loads(student['face_encoding'])
                        self.known_face_encodings.append(face_encoding)
                        self.known_face_enrollments.append(student['enrollment_no'])
                        self.known_face_names.append(student['name'])
                    except Exception as e:
                        print(f"Error loading face for {student['enrollment_no']}: {e}")
                
                print(f"✅ Loaded {len(self.known_face_encodings)} known faces")
                
            except Exception as e:
                print(f"Error loading faces: {e}")
            finally:
                cursor.close()
                conn.close()
    
    def extract_face_encoding(self, image_data):
        """Single photo se face encoding extract karo"""
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            rgb_image = np.array(image.convert('RGB'))
            
            # Face detect karo
            face_locations = face_recognition.face_locations(rgb_image, model="hog")
            
            if len(face_locations) == 0:
                return None, "No face detected in the image"
            
            if len(face_locations) > 1:
                return None, "Multiple faces detected. Please upload a photo with only one face."
            
            # Face encoding extract karo
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if len(face_encodings) == 0:
                return None, "Could not extract face features"
            
            return face_encodings[0], "Success"
            
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def recognize_faces_in_group_photo(self, image_data):
        """Group photo se faces recognize karo"""
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            rgb_image = np.array(image.convert('RGB'))
            
            # Saare faces detect karo group photo mein
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            recognized_students = []
            
            for i, face_encoding in enumerate(face_encodings):
                if len(self.known_face_encodings) > 0:
                    # Compare with known faces
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, 0.6)
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            confidence = 1 - face_distances[best_match_index]
                            if confidence > 0.6:  # Confidence threshold
                                recognized_students.append({
                                    'enrollment_no': self.known_face_enrollments[best_match_index],
                                    'name': self.known_face_names[best_match_index],
                                    'confidence': round(confidence * 100, 2)
                                })
                                print(f"✅ Recognized: {self.known_face_names[best_match_index]} ({confidence:.2%})")
            
            return recognized_students, len(face_locations)
            
        except Exception as e:
            print(f"❌ Recognition error: {e}")
            return [], 0
    
    def save_face_encoding(self, enrollment_no, face_encoding):
        """Face encoding database mein save karo"""
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                face_encoding_bytes = pickle.dumps(face_encoding)
                
                # Check if already exists
                cursor.execute('SELECT * FROM face_encodings WHERE enrollment_no = %s', (enrollment_no,))
                if cursor.fetchone():
                    # Update existing
                    cursor.execute('''
                        UPDATE face_encodings 
                        SET face_encoding = %s, updated_at = CURRENT_TIMESTAMP 
                        WHERE enrollment_no = %s
                    ''', (face_encoding_bytes, enrollment_no))
                else:
                    # Insert new
                    cursor.execute('''
                        INSERT INTO face_encodings (enrollment_no, face_encoding) 
                        VALUES (%s, %s)
                    ''', (enrollment_no, face_encoding_bytes))
                
                conn.commit()
                return True, "Face encoding saved successfully"
                
            except Exception as e:
                return False, f"Database error: {str(e)}"
            finally:
                cursor.close()
                conn.close()
        return False, "Database connection failed"

# Global instance
face_system = FaceRecognitionSystem()