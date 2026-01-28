
# Mapping χωρών / γλωσσών σε CID
lang_mapping = {
    'EN': 1,
    'FR': 2,
    'DE': 3,
    'IT': 4,
    'AL': 5,
    'GR': 6,
    'ES': 7,
    'PT': 8,
    'NL': 9,
    'BE': 10,
    'LU': 11,
    'AT': 12,
    'CH': 13,
    'SE': 14,
    'NO': 15,
    'FI': 16,
    'DK': 17,
    'IE': 18,
    'IS': 19,
    'PL': 20,
    'CZ': 21,
    'SK': 22,
    'HU': 23,
    'RO': 24,
    'BG': 25,
    'HR': 26,
    'SI': 27,
    'BA': 28,
    'RS': 29,
    'MK': 30,
    'TR': 31,
    'RU': 32,
    'UA': 33,
    'BY': 34,
    'MD': 35,
    'CY': 36,
    'MT': 37,
    'LT': 38,
    'LV': 39,
    'EE': 40,
    'AD': 41,
    'AM': 42,
    'AZ': 43,
    'GE': 44,
    'LI': 45,
    'MC': 46,
    'SM': 47,
    'VA': 48,
    'ME': 50,

    # Jurisdiction / patent codes
    'EP': 101,
    'US': 102,
    'JP': 103,
    'CN': 104,
    'KR': 105,
    'WO': 106,
    'GB': 107,
    'CA': 108,
    'AU': 109,
}


def log_error(message):
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")


def create_lang_table(cursor, db):
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS state")

        cursor.execute("""
            CREATE TABLE lang (
                CID TINYINT UNSIGNED NOT NULL,
                name VARCHAR(50) NOT NULL,     -- EN, FR, GR
                PRIMARY KEY (CID),
                UNIQUE KEY uq_lang_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db.commit()
        print("[OK] Ο πίνακας lang δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        log_error(f"[CREATE_TABLE_ERROR] lang: {e}")
        raise


def initialize_lang(cursor, db):
    for lang, cid in lang_mapping.items():
        try:
            cursor.execute("SELECT COUNT(*) FROM lang WHERE CID = %s", (cid,))
            if cursor.fetchone()[0] == 0:
                try:
                    cursor.execute(
                        "INSERT INTO lang (CID, name) VALUES (%s, %s)",
                        (cid, lang)
                    )
                except Exception as insert_err:
                    log_error(
                        f"[INSERT_ERROR] CID: {cid}, lang: {lang}, error: {insert_err}"
                    )
        except Exception as select_err:
            log_error(
                f"[SELECT_ERROR] CID: {cid}, lang: {lang}, error: {select_err}"
            )

    try:
        db.commit()
        print("[OK] Ο πίνακας lang αρχικοποιήθηκε")
    except Exception as commit_err:
        db.rollback()
        log_error(f"[COMMIT_ERROR] initialize_lang commit failed: {commit_err}")
        raise

