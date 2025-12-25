#
# import logging
#
# # Ρύθμιση logging αν δεν υπάρχει ήδη
# logging.basicConfig(filename='init.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#
# role_mapping = {
#     'applicant': 1,
#     'inventor': 2,
#     'agent': 3
# }
#
# def initialize_role(cursor, db):
#     for name, rid in role_mapping.items():
#         cursor.execute("SELECT COUNT(*) FROM role WHERE RID = %s", (rid,))
#         if cursor.fetchone()[0] == 0:
#             logging.info(f"➕ Εισαγωγή στον πίνακα role: ({rid}, '{name}')")
#             cursor.execute("INSERT INTO role (RID, name) VALUES (%s, %s)", (rid, name))
#         else:
#             logging.info(f"✔️ Ο ρόλος '{name}' (RID={rid}) υπάρχει ήδη.")
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
# Σταθερές τιμές role
# -------------------------------------------------
role_mapping = {
    'applicant': 1,
    'inventor': 2,
    'agent': 3
}

# -------------------------------------------------
# CREATE TABLE role
# -------------------------------------------------
def create_role_table(cursor, db):
    try:
        cursor.execute("""
            DROP TABLE IF EXISTS role
        """)

        cursor.execute("""
            CREATE TABLE role (
                RID INT NOT NULL,
                name VARCHAR(30) NOT NULL,
                PRIMARY KEY (RID),
                UNIQUE (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("[OK] Ο πίνακας role δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στο create_role_table: %s", e)


# -------------------------------------------------
# INSERT αρχικών δεδομένων
# -------------------------------------------------
def initialize_role(cursor, db):
    try:
        for name, rid in role_mapping.items():
            cursor.execute(
                "SELECT COUNT(*) FROM role WHERE RID = %s",
                (rid,)
            )
            if cursor.fetchone()[0] == 0:
                logging.info(f"➕ Εισαγωγή στον πίνακα role: ({rid}, '{name}')")
                cursor.execute(
                    "INSERT INTO role (RID, name) VALUES (%s, %s)",
                    (rid, name)
                )
            else:
                logging.info(f"✔️ Ο ρόλος '{name}' (RID={rid}) υπάρχει ήδη.")

        db.commit()
        print("[OK] Ο πίνακας role αρχικοποιήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στην initialize_role: %s", e)
