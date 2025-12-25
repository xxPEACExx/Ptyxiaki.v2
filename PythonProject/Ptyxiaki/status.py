#
# status_mapping = {
#     'corrected': 1,
#     'deleted': 2
# }
#
# def log_error(message):
#     with open("errors.log", "a", encoding="utf-8") as f:
#         f.write(message + "\n")
#
# def initialize_status(cursor, db):
#     for name, sid in status_mapping.items():
#         try:
#             cursor.execute("SELECT COUNT(*) FROM status WHERE SID = %s", (sid,))
#             if cursor.fetchone()[0] == 0:
#                 try:
#                     cursor.execute("INSERT INTO status (SID, name) VALUES (%s, %s)", (sid, name))
#                 except Exception as insert_err:
#                     log_error(f"[INSERT_ERROR] SID: {sid}, name: {name}, error: {insert_err}")
#                     continue
#         except Exception as select_err:
#             log_error(f"[SELECT_ERROR] SID: {sid}, name: {name}, error: {select_err}")
#             continue
#     try:
#         db.commit()
#     except Exception as commit_err:
#         db.rollback()
#         log_error(f"[COMMIT_ERROR] initialize_status commit failed: {commit_err}")
#

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
        cursor.execute("""
            DROP TABLE IF EXISTS status
        """)

        cursor.execute("""
            CREATE TABLE status (
                SID INT NOT NULL,
                name VARCHAR(30) NOT NULL,
                PRIMARY KEY (SID),
                UNIQUE (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("[OK] Ο πίνακας status δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στο create_status_table: %s", e)


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
