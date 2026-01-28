

import logging

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(
    filename='errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# -------------------------------------------------
# Σταθερές τιμές format
# -------------------------------------------------
format_mapping = {
    'epo': 1,
    'original': 2,
    'intermediate': 3
}

# -------------------------------------------------
# CREATE TABLE format
# -------------------------------------------------
def create_format_table(cursor, db):
    try:
        cursor.execute("""
            DROP TABLE IF EXISTS format
        """)

        cursor.execute("""
            CREATE TABLE format (
                FID INT NOT NULL,
                name VARCHAR(50) NOT NULL,
                PRIMARY KEY (FID),
                UNIQUE (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("Δημιουργήθηκε ο πίνακας FORMAT")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στο create_format_table: %s", e)


# -------------------------------------------------
# INSERT αρχικών δεδομένων
# -------------------------------------------------
def initialize_format(cursor, db):
    try:
        for name, fid in format_mapping.items():
            cursor.execute(
                "SELECT COUNT(*) FROM format WHERE FID = %s",
                (fid,)
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO format (FID, name) VALUES (%s, %s)",
                    (fid, name)
                )

        db.commit()
        print("Aρχικοποιήθηκε o πίνακας FORMAT")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στην initialize_format: %s", e)
