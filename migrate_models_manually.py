import sqlite3
import os
import logging
from app import app, db
from datetime import datetime
from models import User, Student, Instructor, Course, Enrollment, Lesson, Assignment
from models import Submission, Grade, Schedule, ForumTopic, ForumResponse, ForumLike

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Find the database file
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'instance', 'lms.db')

def check_constraint_exists(cursor, table_name, constraint_name):
    """Check if a constraint already exists in a table"""
    cursor.execute(f"""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='{table_name}' AND sql LIKE '%{constraint_name}%';
    """)
    return bool(cursor.fetchone())

def check_table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute(f"""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='{table_name}';
    """)
    return bool(cursor.fetchone())

def backup_database():
    """Create a backup of the database before making changes"""
    backup_path = f"{db_path}.bak_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"Created backup of database at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return False

def migrate_models_manually():
    """Manually migrate the database to reflect changes in models.py"""
    # First, create a backup
    if not backup_database():
        logger.error("Aborting migration as backup creation failed")
        return False
        
    conn = None
    try:
        # Connect to the database
        logger.info(f"Using database at {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if ForumLike table has the unique constraint
        has_constraint = check_constraint_exists(cursor, "forum_like", "unique_response_like")
        
        if not has_constraint:
            logger.info("Adding unique constraint to forum_like table")
            # Create a new table with the constraint
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forum_like_new (
                    id INTEGER PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (response_id) REFERENCES forum_response(id),
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    UNIQUE (response_id, user_id) ON CONFLICT REPLACE
                );
            """)
            
            # Check if the forum_like table exists before trying to copy data
            if check_table_exists(cursor, "forum_like"):
                # Copy data from the old table to the new one
                cursor.execute("""
                    INSERT OR IGNORE INTO forum_like_new (id, created_at, response_id, user_id)
                    SELECT id, created_at, response_id, user_id FROM forum_like;
                """)
                
                # Drop the old table and rename the new one
                cursor.execute("DROP TABLE forum_like;")
                cursor.execute("ALTER TABLE forum_like_new RENAME TO forum_like;")
                logger.info("Successfully migrated forum_like table with unique constraint")
        
        # Commit the changes
        conn.commit()
        logger.info("Manual migration completed successfully!")
        
        # Now use the ORM to create any new tables or columns
        with app.app_context():
            logger.info("Applying any remaining model changes with ORM...")
            db.create_all()
            db.session.commit()
            logger.info("ORM migration completed successfully!")
        
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
    success = migrate_models_manually()
    if success:
        print("Database migration completed successfully!")
    else:
        print("Database migration failed. Check the logs for details.")
