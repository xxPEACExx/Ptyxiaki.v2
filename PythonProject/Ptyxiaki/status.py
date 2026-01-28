
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
# Σταθερές τιμές status
# -------------------------------------------------
status_mapping = {
    'corrected': 1,
    'deleted': 2
}

# -------------------------------------------------
# CREATE TABLE status
# -------------------------------------------------
def create_status_table(cursor, db):
    try:
        print("[DEBUG] create_status_table: START")

        print("[DEBUG] Disabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        print("[DEBUG] Dropping table status if exists")
        cursor.execute("DROP TABLE IF EXISTS status")

        print("[DEBUG] Creating table status")
        cursor.execute("""
            CREATE TABLE status (
                SID INT UNSIGNED NOT NULL,
                name VARCHAR(30) NOT NULL,

                PRIMARY KEY (SID),
                UNIQUE KEY uq_status_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        print("[DEBUG] Enabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        db.commit()
        print("[OK] Ο πίνακας status δημιουργήθηκε επιτυχώς")

    except Exception as e:
        print("[ERROR] create_status_table FAILED")
        print("[MYSQL ERROR]", e)

        db.rollback()

        import logging
        import traceback
        logging.error(
            "[STATUS_TABLE_CREATE_ERROR]\n%s",
            traceback.format_exc()
        )

        raise



# -------------------------------------------------
# INSERT αρχικών δεδομένων
# -------------------------------------------------
def initialize_status(cursor, db):
    for name, sid in status_mapping.items():
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM status WHERE SID = %s",
                (sid,)
            )
            if cursor.fetchone()[0] == 0:
                try:
                    cursor.execute(
                        "INSERT INTO status (SID, name) VALUES (%s, %s)",
                        (sid, name)
                    )
                except Exception as insert_err:
                    logging.error(
                        "[INSERT_ERROR] SID: %s, name: %s, error: %s",
                        sid, name, insert_err
                    )
                    continue
        except Exception as select_err:
            logging.error(
                "[SELECT_ERROR] SID: %s, name: %s, error: %s",
                sid, name, select_err
            )
            continue

    try:
        db.commit()
        print("[OK] Ο πίνακας status αρχικοποιήθηκε")
    except Exception as commit_err:
        db.rollback()
        logging.error(
            "[COMMIT_ERROR] initialize_status commit failed: %s",
            commit_err
        )
