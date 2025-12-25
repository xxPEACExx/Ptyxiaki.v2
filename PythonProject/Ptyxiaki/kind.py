#
# import logging
#
# # Ρύθμιση του logging για καταγραφή σε αρχείο
# logging.basicConfig(filename='errors.log', level=logging.ERROR,
#                     format='%(asctime)s - %(levelname)s - %(message)s')
#
# kind_mapping = {
#     'A1': 1, 'A': 2, 'W': 3, 'P': 4, 'U': 5, 'B1': 6, 'F': 7, 'A2': 8,
#     'B': 9, 'C': 10, 'C1': 11, 'B2': 12, 'U1': 13, 'C2': 14, 'T2': 15,
#     'A4': 16, 'S': 17, 'A3': 18, 'Y': 19, 'T5': 20, 'B3': 21, 'A5': 22,
#     'B4': 23, 'E': 24, 'A7': 25, 'Q': 26, 'Y1': 27, 'A9': 28, 'B8': 29,
#     'B9': 30, 'C3': 31, 'A8': 32, 'P1': 33, 'P2': 34, 'U2': 35, 'Y2': 36,
#     'T3': 37, 'I5': 38, 'K1': 39, 'A6': 40, 'B5': 41, 'H': 42, 'L': 43,
#     'K': 44, 'B6': 45, 'S1': 46, 'T1': 47, 'R': 48, 'T': 49, 'Z2': 50,
#     'C5': 51, 'K5': 52, 'D0': 53, 'M': 54, 'D1': 55, 'K4': 56, 'A0': 57,
#     'Z': 58, 'K2': 59, 'I4': 60, 'X': 61, 'U3': 62, 'E1': 63, 'D': 64,
#     'U4': 65, 'P3': 66
# }
#
# def initialize_kind(cursor, db):
#     try:
#         for kind_name, kid in kind_mapping.items():
#             cursor.execute("SELECT COUNT(*) FROM kind WHERE KID = %s", (kid,))
#             if cursor.fetchone()[0] == 0:
#                 cursor.execute(
#                     "INSERT INTO kind (KID, name) VALUES (%s, %s)",
#                     (kid, kind_name)
#                 )
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         logging.error("Σφάλμα στην initialize_kind: %s", e)
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
# Σταθερές τιμές kind
# -------------------------------------------------
kind_mapping = {
    'A1': 1, 'A': 2, 'W': 3, 'P': 4, 'U': 5, 'B1': 6, 'F': 7, 'A2': 8,
    'B': 9, 'C': 10, 'C1': 11, 'B2': 12, 'U1': 13, 'C2': 14, 'T2': 15,
    'A4': 16, 'S': 17, 'A3': 18, 'Y': 19, 'T5': 20, 'B3': 21, 'A5': 22,
    'B4': 23, 'E': 24, 'A7': 25, 'Q': 26, 'Y1': 27, 'A9': 28, 'B8': 29,
    'B9': 30, 'C3': 31, 'A8': 32, 'P1': 33, 'P2': 34, 'U2': 35, 'Y2': 36,
    'T3': 37, 'I5': 38, 'K1': 39, 'A6': 40, 'B5': 41, 'H': 42, 'L': 43,
    'K': 44, 'B6': 45, 'S1': 46, 'T1': 47, 'R': 48, 'T': 49, 'Z2': 50,
    'C5': 51, 'K5': 52, 'D0': 53, 'M': 54, 'D1': 55, 'K4': 56, 'A0': 57,
    'Z': 58, 'K2': 59, 'I4': 60, 'X': 61, 'U3': 62, 'E1': 63, 'D': 64,
    'U4': 65, 'P3': 66
}

# -------------------------------------------------
# CREATE TABLE kind
# -------------------------------------------------
def create_kind_table(cursor, db):
    try:
        cursor.execute("""
            DROP TABLE IF EXISTS kind
        """)

        cursor.execute("""
            CREATE TABLE kind (
                KID INT NOT NULL,
                name VARCHAR(10) NOT NULL,
                PRIMARY KEY (KID),
                UNIQUE (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("[OK] Ο πίνακας kind δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στο create_kind_table: %s", e)


# -------------------------------------------------
# INSERT αρχικών δεδομένων
# -------------------------------------------------
def initialize_kind(cursor, db):
    try:
        for kind_name, kid in kind_mapping.items():
            cursor.execute(
                "SELECT COUNT(*) FROM kind WHERE KID = %s",
                (kid,)
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO kind (KID, name) VALUES (%s, %s)",
                    (kid, kind_name)
                )

        db.commit()
        print("[OK] Ο πίνακας kind αρχικοποιήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στην initialize_kind: %s", e)
