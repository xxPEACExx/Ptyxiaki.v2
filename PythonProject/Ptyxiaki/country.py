import logging


country_mapping = {
    'EP': 1,
    'WO': 2,
    'US': 3
}


def create_country_table(cursor, db):
    try:
        print("[DEBUG] create_country_table: START")

        print("[DEBUG] Disabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        print("[DEBUG] Dropping table country if exists")
        cursor.execute("DROP TABLE IF EXISTS country")

        print("[DEBUG] Creating table country")
        cursor.execute("""
            CREATE TABLE country (
                CID TINYINT UNSIGNED NOT NULL,
                name VARCHAR(10) NOT NULL,

                PRIMARY KEY (CID),
                UNIQUE KEY uq_country_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        print("[DEBUG] Enabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        db.commit()
        print("[OK] Ο πίνακας country δημιουργήθηκε επιτυχώς")

    except Exception as e:
        print("[ERROR] create_country_table FAILED")
        print("[MYSQL ERROR]", e)

        db.rollback()

        import logging
        import traceback
        logging.error(
            "Σφάλμα στο create_country_table:\n%s",
            traceback.format_exc()
        )

        raise


def initialize_country(cursor, db):
    try:
        for country_name, cid in country_mapping.items():
            cursor.execute(
                "SELECT COUNT(*) FROM country WHERE CID = %s",
                (cid,)
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO country (CID, name) VALUES (%s, %s)",
                    (cid, country_name)
                )

        db.commit()
        print("[OK] Ο πίνακας country αρχικοποιήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στην initialize_country: %s", e)
