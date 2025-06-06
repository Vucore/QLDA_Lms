import sqlite3
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Find the database file
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'instance', 'lms.db')

def migrate_database():
    """
    Migrate the database to fix the column name issue:
    - Rename 'enrollment_date' to 'enrolled_at' in the enrollment table
    - Add 'approved_at' column if it doesn't exist
    """
    conn = None
    try:
        # Verify the database exists
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at {db_path}")
            return False

        logger.info(f"Using database at {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='enrollment'")
        if not cursor.fetchone():
            logger.error("Enrollment table does not exist")
            return False
        
        # Get current schema
        cursor.execute("PRAGMA table_info(enrollment)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        logger.info(f"Current columns: {column_names}")
        
        # If we have enrollment_date but not enrolled_at, we need to fix it
        if 'enrollment_date' in column_names and 'enrolled_at' not in column_names:
            # SQLite doesn't support ALTER TABLE RENAME COLUMN
            # We need to create a new table, copy data, and replace the old table
            
            # Drop enrollment_new if it exists
            cursor.execute("DROP TABLE IF EXISTS enrollment_new")
            
            # Create new table with correct schema
            cursor.execute('''
            CREATE TABLE enrollment_new (
                id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                enrolled_at DATETIME,
                status VARCHAR(20),
                approved_at DATETIME,
                FOREIGN KEY (student_id) REFERENCES student (id),
                FOREIGN KEY (course_id) REFERENCES course (id)
            )
            ''')
            
            # Copy data
            cursor.execute('''
            INSERT INTO enrollment_new (id, student_id, course_id, enrolled_at, status, approved_at)
            SELECT id, student_id, course_id, enrollment_date, status, NULL FROM enrollment
            ''')
            
            # Drop old table
            cursor.execute("DROP TABLE enrollment")
            
            # Rename new table
            cursor.execute("ALTER TABLE enrollment_new RENAME TO enrollment")
            
            logger.info("Successfully renamed enrollment_date to enrolled_at")
        elif 'enrolled_at' not in column_names:
            # If neither column exists, create enrolled_at column
            cursor.execute("ALTER TABLE enrollment ADD COLUMN enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            logger.info("Added enrolled_at column")
        
        # Check if approved_at exists, add if not
        cursor.execute("PRAGMA table_info(enrollment)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'approved_at' not in column_names:
            cursor.execute("ALTER TABLE enrollment ADD COLUMN approved_at DATETIME")
            # Set approved_at to the same as enrolled_at for approved enrollments
            cursor.execute("UPDATE enrollment SET approved_at = enrolled_at WHERE status = 'approved'")
            logger.info("Added approved_at column")
        
        # Check if 'full_name' column exists in 'user' table
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        if 'full_name' in column_names:
            cursor.execute("ALTER TABLE user DROP COLUMN full_name")
            logger.info("Dropped 'full_name' column from 'user' table")

        conn.commit()
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database()