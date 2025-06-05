from app import app, db
from models import ForumTopic, ForumResponse, ForumLike

def migrate_forum_tables():
    """
    Thêm các bảng mới liên quan đến diễn đàn vào database
    """
    print("Migrating forum tables...")
    with app.app_context():
        db.create_all()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_forum_tables()
