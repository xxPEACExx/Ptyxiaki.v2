import logging


country_mapping = {
    'EP': 1,
    'WO': 2,
    'US': 3
}


def create_country_table(cursor, db):
    try:
        cursor.execute("""
            DROP TABLE IF EXISTS country
        """)

        cursor.execute("""
            CREATE TABLE country (
                CID TINYINT NOT NULL,
                name VARCHAR(10) NOT NULL,
                PRIMARY KEY (CID),
                UNIQUE (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("[OK] Ο πίνακας country δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στο create_country_table: %s", e)


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
