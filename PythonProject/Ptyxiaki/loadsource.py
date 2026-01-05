#
# import logging
#
# # Ρύθμιση logging για καταγραφή σε αρχείο
# logging.basicConfig(filename='errors.log', level=logging.ERROR,
#                     format='%(asctime)s - %(levelname)s - %(message)s')
#
# loadsource_mapping = {
#     'docdb': 1,
#     'patent-office': 2,
#     'ipcr': 3,
# }
#
# def initialize_loadsource(cursor, db):
#     try:
#         for name, lid in loadsource_mapping.items():
#             cursor.execute("SELECT COUNT(*) FROM loadsource WHERE LID = %s", (lid,))
#             if cursor.fetchone()[0] == 0:
#                 print(f"[INFO] Εισαγωγή: ({lid}, '{name}') στον πίνακα loadsource")
#                 cursor.execute("INSERT INTO loadsource (LID, name_loadsource) VALUES (%s, %s)", (lid, name))
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         logging.error("Σφάλμα στην initialize_loadsource: %s", e)

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
# Σταθερές τιμές loadsource
# -------------------------------------------------
loadsource_mapping = {
    'docdb': 1,
    'patent-office': 2,
    'ipcr': 3
}

# -------------------------------------------------
# CREATE TABLE loadsource
# -------------------------------------------------
def create_loadsource_table(cursor, db):
    try:
        cursor.execute("""
            DROP TABLE IF EXISTS loadsource
        """)

        cursor.execute("""
            CREATE TABLE loadsource (
                LID tinyint NOT NULL,
                name_loadsource VARCHAR(50) NOT NULL,
                PRIMARY KEY (LID),
                UNIQUE (name_loadsource)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("[OK] Ο πίνακας loadsource δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στο create_loadsource_table: %s", e)


# -------------------------------------------------
# INSERT αρχικών δεδομένων
# -------------------------------------------------
def initialize_loadsource(cursor, db):
    try:
        for name, lid in loadsource_mapping.items():
            cursor.execute(
                "SELECT COUNT(*) FROM loadsource WHERE LID = %s",
                (lid,)
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO loadsource (LID, name_loadsource) VALUES (%s, %s)",
                    (lid, name)
                )

        db.commit()
        print("[OK] Ο πίνακας loadsource αρχικοποιήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στην initialize_loadsource: %s", e)
