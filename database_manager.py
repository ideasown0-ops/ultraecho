"""
SQLite Database Manager
Handles patient records, exam history, and analysis storage
"""

import sqlite3
import logging
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger("ultrasound")


@dataclass
class Patient:
    """Patient record"""
    patient_id: str
    name: str
    age: int
    gender: str
    contact: str
    medical_history: str
    created_at: str = None
    updated_at: str = None


@dataclass
class Examination:
    """Examination record"""
    exam_id: str
    patient_id: str
    exam_type: str  # "abdominal", "obstetric", etc.
    exam_date: str
    modality: str  # "ultrasound"
    indication: str
    findings: str
    status: str  # "completed", "pending", "archived"
    created_at: str = None
    updated_at: str = None


@dataclass
class AnalysisReport:
    """Analysis report for an examination"""
    report_id: str
    exam_id: str
    ai_findings: str
    detected_organs: List[str]
    quality_score: float
    recommendations: str
    created_at: str = None


class DatabaseManager:
    """Manages SQLite database for ultrasound application"""
    
    def __init__(self, db_path: str = "ultrasound.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self.initialize_database()
    
    def initialize_database(self):
        """Create database and initialize tables"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            cursor = self.connection.cursor()
            
            # Create tables
            self._create_tables(cursor)
            self.connection.commit()
            
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _create_tables(self, cursor):
        """Create all required tables"""
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                contact TEXT,
                medical_history TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Examinations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS examinations (
                exam_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                exam_type TEXT,
                exam_date TIMESTAMP,
                modality TEXT,
                indication TEXT,
                findings TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        ''')
        
        # Analysis reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_reports (
                report_id TEXT PRIMARY KEY,
                exam_id TEXT NOT NULL,
                ai_findings TEXT,
                detected_organs TEXT,
                quality_score REAL,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
            )
        ''')
        
        # Captured frames table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS captured_frames (
                frame_id TEXT PRIMARY KEY,
                exam_id TEXT,
                frame_path TEXT,
                timestamp TIMESTAMP,
                quality_score REAL,
                organs_detected TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
            )
        ''')
        
        # Examination media table
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS examination_media ("
            "media_id TEXT PRIMARY KEY,"
            "exam_id TEXT NOT NULL,"
            "media_type TEXT NOT NULL,"
            "file_path TEXT NOT NULL,"
            "created_at TEXT NOT NULL,"
            "FOREIGN KEY (exam_id) REFERENCES examinations (exam_id)"
            ")"
        )

        # AI Analysis history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis_history (
                analysis_id TEXT PRIMARY KEY,
                frame_id TEXT,
                exam_id TEXT,
                detected_organs TEXT,
                quality_score REAL,
                frame_score REAL,
                processing_time_ms REAL,
                models_used TEXT,
                is_best_frame INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (frame_id) REFERENCES captured_frames(frame_id),
                FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
            )
        ''')
        
        logger.info("All tables created successfully")
    
    # Patient Management
    def add_patient(self, patient: Patient) -> bool:
        """Add a new patient"""
        try:
            cursor = self.connection.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO patients 
                (patient_id, name, age, gender, contact, medical_history, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient.patient_id, patient.name, patient.age,
                patient.gender, patient.contact, patient.medical_history,
                now, now
            ))
            
            self.connection.commit()
            logger.info(f"Patient {patient.patient_id} added")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add patient: {e}")
            return False
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Retrieve patient information"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,))
            row = cursor.fetchone()
            
            if row:
                return Patient(
                    patient_id=row['patient_id'],
                    name=row['name'],
                    age=row['age'],
                    gender=row['gender'],
                    contact=row['contact'],
                    medical_history=row['medical_history'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get patient: {e}")
            return None
    
    def list_patients(self) -> List[Patient]:
        """List all patients"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM patients ORDER BY created_at DESC')
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append(Patient(
                    patient_id=row['patient_id'],
                    name=row['name'],
                    age=row['age'],
                    gender=row['gender'],
                    contact=row['contact'],
                    medical_history=row['medical_history'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            
            return patients
            
        except Exception as e:
            logger.error(f"Failed to list patients: {e}")
            return []
    
    # Examination Management
    def add_examination(self, exam: Examination) -> bool:
        """Add a new examination"""
        try:
            cursor = self.connection.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO examinations
                (exam_id, patient_id, exam_type, exam_date, modality, indication, findings, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                exam.exam_id, exam.patient_id, exam.exam_type,
                exam.exam_date, exam.modality, exam.indication,
                exam.findings, exam.status, now, now
            ))
            
            self.connection.commit()
            logger.info(f"Examination {exam.exam_id} added")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add examination: {e}")
            return False
    
    def get_patient_examinations(self, patient_id: str) -> List[Examination]:
        """Get all examinations for a patient"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                'SELECT * FROM examinations WHERE patient_id = ? ORDER BY exam_date DESC',
                (patient_id,)
            )
            rows = cursor.fetchall()
            
            exams = []
            for row in rows:
                exams.append(Examination(
                    exam_id=row['exam_id'],
                    patient_id=row['patient_id'],
                    exam_type=row['exam_type'],
                    exam_date=row['exam_date'],
                    modality=row['modality'],
                    indication=row['indication'],
                    findings=row['findings'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            
            return exams
            
        except Exception as e:
            logger.error(f"Failed to get examinations: {e}")
            return []
    
    # Analysis Report Management
    def add_analysis_report(self, report: AnalysisReport) -> bool:
        """Add an analysis report"""
        try:
            cursor = self.connection.cursor()
            now = datetime.now().isoformat()
            
            organs_json = json.dumps(report.detected_organs)
            
            cursor.execute('''
                INSERT INTO analysis_reports
                (report_id, exam_id, ai_findings, detected_organs, quality_score, recommendations, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.report_id, report.exam_id, report.ai_findings,
                organs_json, report.quality_score, report.recommendations, now
            ))
            
            self.connection.commit()
            logger.info(f"Analysis report {report.report_id} added")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add analysis report: {e}")
            return False
    
    def get_exam_report(self, exam_id: str) -> Optional[AnalysisReport]:
        """Get analysis report for an examination"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM analysis_reports WHERE exam_id = ?', (exam_id,))
            row = cursor.fetchone()
            
            if row:
                return AnalysisReport(
                    report_id=row['report_id'],
                    exam_id=row['exam_id'],
                    ai_findings=row['ai_findings'],
                    detected_organs=json.loads(row['detected_organs']),
                    quality_score=row['quality_score'],
                    recommendations=row['recommendations'],
                    created_at=row['created_at']
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get report: {e}")
            return None
    
    # Captured Frames Management
    def add_captured_frame(self, frame_id: str, exam_id: str, frame_path: str,
                          quality_score: float, organs_detected: List[str]) -> bool:
        """Add a captured frame record"""
        try:
            cursor = self.connection.cursor()
            now = datetime.now().isoformat()
            organs_json = json.dumps(organs_detected)
            
            cursor.execute('''
                INSERT INTO captured_frames
                (frame_id, exam_id, frame_path, timestamp, quality_score, organs_detected, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                frame_id, exam_id, frame_path, now, quality_score, organs_json, now
            ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add captured frame: {e}")
            return False
    
    # AI Analysis History
    def add_ai_analysis(self, analysis_id: str, frame_id: str, exam_id: str,
                       detected_organs: List[str], quality_score: float,
                       frame_score: float, processing_time: float,
                       models_used: List[str], is_best_frame: bool) -> bool:
        """Add AI analysis record"""
        try:
            cursor = self.connection.cursor()
            now = datetime.now().isoformat()
            
            organs_json = json.dumps(detected_organs)
            models_json = json.dumps(models_used)
            
            cursor.execute('''
                INSERT INTO ai_analysis_history
                (analysis_id, frame_id, exam_id, detected_organs, quality_score, frame_score,
                 processing_time_ms, models_used, is_best_frame, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis_id, frame_id, exam_id, organs_json, quality_score,
                frame_score, processing_time, models_json, int(is_best_frame), now
            ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add AI analysis: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM patients')
            patient_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM examinations')
            exam_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM captured_frames')
            frame_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT AVG(quality_score) as avg_quality FROM ai_analysis_history')
            avg_quality = cursor.fetchone()['avg_quality'] or 0
            
            return {
                "total_patients": patient_count,
                "total_examinations": exam_count,
                "total_frames": frame_count,
                "average_quality_score": avg_quality
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def add_examination_media(
        self,
        media_id: str,
        exam_id: str,
        media_type: str,
        file_path: str
    ) -> bool:
        """Register a media file belonging to an examination."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO examination_media "
                "(media_id, exam_id, media_type, file_path, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    media_id,
                    exam_id,
                    media_type,
                    file_path,
                    datetime.now().isoformat()
                )
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding examination media: {e}")
            return False

    def get_examination_media(
        self,
        exam_id: str,
        media_type: str = None
    ):
        """Return media files belonging to an examination."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if media_type:
                cursor.execute(
                    "SELECT media_id, exam_id, media_type, file_path, "
                    "created_at "
                    "FROM examination_media "
                    "WHERE exam_id = ? AND media_type = ? "
                    "ORDER BY created_at DESC",
                    (exam_id, media_type)
                )
            else:
                cursor.execute(
                    "SELECT media_id, exam_id, media_type, file_path, "
                    "created_at "
                    "FROM examination_media "
                    "WHERE exam_id = ? "
                    "ORDER BY created_at DESC",
                    (exam_id,)
                )

            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting examination media: {e}")
            return []

    def get_all_examinations(self):
        """Return all examinations ordered by newest first."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM examinations "
                "ORDER BY exam_date DESC"
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting all examinations: {e}")
            return []

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test database
    db = DatabaseManager("test_ultrasound.db")
    
    # Add test patient
    patient = Patient(
        patient_id="P001",
        name="Ahmed Ali",
        age=45,
        gender="M",
        contact="0123456789",
        medical_history="Hypertension"
    )
    db.add_patient(patient)
    
    # List patients
    print("\nPatients:")
    for p in db.list_patients():
        print(f"  {p.patient_id}: {p.name}")
    
    # Get statistics
    print("\nDatabase Statistics:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    db.close()
