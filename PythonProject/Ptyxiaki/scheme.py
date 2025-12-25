#
# import logging
#
# logging.basicConfig(filename='init.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#
# scheme_mapping = {
#     'CPC': 1,
#     'EC': 2,
#     'ICO': 3
# }
#
# def initialize_scheme(cursor, db):
#     for scheme_name, sid in scheme_mapping.items():
#         cursor.execute("SELECT COUNT(*) FROM scheme WHERE SID = %s", (sid,))
#         if cursor.fetchone()[0] == 0:
#             logging.info(f"➕ Εισαγωγή scheme: ({sid}, '{scheme_name}')")
#             cursor.execute(
#                 "INSERT INTO scheme (SID, name) VALUES (%s, %s)",
#                 (sid, scheme_name)
#             )
#         else:
#             logging.info(f"✔️ Το scheme '{scheme_name}' (SID={sid}) υπάρχει ήδη.")
#     db.commit()

import logging

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(
    filename='init.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# -------------------------------------------------
# Σταθερές τιμές scheme
# -------------------------------------------------
scheme_mapping = {
    'CPC': 1,
    'EC': 2,
    'ICO': 3
}

# -------------------------------------------------
# CREATE TABLE scheme
# -------------------------------------------------
def create_scheme_table(cursor, db):
    try:
        cursor.execute("""
            DROP TABLE IF EXISTS scheme
        """)

        cursor.execute("""
            CREATE TABLE scheme (
                SID INT NOT NULL,
                name VARCHAR(20) NOT NULL,
                PRIMARY KEY (SID),
                UNIQUE (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("[OK] Ο πίνακας scheme δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στο create_scheme_table: %s", e)


# -------------------------------------------------
# INSERT αρχικών δεδομένων
# -------------------------------------------------
def initialize_scheme(cursor, db):
    try:
        for scheme_name, sid in scheme_mapping.items():
            cursor.execute(
                "SELECT COUNT(*) FROM scheme WHERE SID = %s",
                (sid,)
            )
            if cursor.fetchone()[0] == 0:
                logging.info(f"➕ Εισαγωγή scheme: ({sid}, '{scheme_name}')")
                cursor.execute(
                    "INSERT INTO scheme (SID, name) VALUES (%s, %s)",
                    (sid, scheme_name)
                )
            else:
                logging.info(f"✔️ Το scheme '{scheme_name}' (SID={sid}) υπάρχει ήδη.")

        db.commit()
        print("[OK] Ο πίνακας scheme αρχικοποιήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στην initialize_scheme: %s", e)
