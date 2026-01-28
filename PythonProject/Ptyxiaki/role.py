

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
        print("[DEBUG] create_role_table: START")

        print("[DEBUG] Disabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        print("[DEBUG] Dropping table role if exists")
        cursor.execute("DROP TABLE IF EXISTS role")

        print("[DEBUG] Creating table role")
        cursor.execute("""
            CREATE TABLE role (
                RID INT UNSIGNED NOT NULL,
                name VARCHAR(30) NOT NULL,

                PRIMARY KEY (RID),
                UNIQUE KEY uq_role_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        print("[DEBUG] Enabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        db.commit()
        print("[OK] Ο πίνακας role δημιουργήθηκε επιτυχώς")

    except Exception as e:
        print("[ERROR] create_role_table FAILED")
        print("[MYSQL ERROR]", e)

        db.rollback()

        import logging
        import traceback
        logging.error(
            "[ROLE_TABLE_CREATE_ERROR]\n%s",
            traceback.format_exc()
        )

        raise


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
