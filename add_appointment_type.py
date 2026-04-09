"""One-time script to add appointment_type column to appointments table."""
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE appointments ADD COLUMN appointment_type VARCHAR(20) DEFAULT 'In-person'"
            ))
            conn.commit()
            print("OK: Column appointment_type added successfully.")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
                print("INFO: Column already exists, skipping.")
            else:
                raise
