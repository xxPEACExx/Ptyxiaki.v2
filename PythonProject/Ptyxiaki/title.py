
import logging
import traceback
from lang import lang_mapping


# -------------------------------------------------
# LOGGING
# -------------------------------------------------
logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# -------------------------------------------------
# CREATE TABLE title
# ΜΟΝΟ FK: DID -> document(DID)
# -------------------------------------------------
def create_title_table(cursor, db):
    try:
        print("[DEBUG] create_title_table: START")

        print("[DEBUG] Disabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        print("[DEBUG] Dropping table title if exists")
        cursor.execute("DROP TABLE IF EXISTS title")

        print("[DEBUG] Creating table title")
        cursor.execute("""
            CREATE TABLE title (
                tID INT UNSIGNED NOT NULL AUTO_INCREMENT,
                DID INT UNSIGNED NOT NULL,

                title_text VARCHAR(255),
                lang TINYINT UNSIGNED,

                title_chars_count SMALLINT UNSIGNED,
                title_words_count SMALLINT UNSIGNED,

                PRIMARY KEY (tID),

                KEY idx_title_DID (DID),
                KEY idx_title_lang (lang),

                CONSTRAINT fk_title_document
                    FOREIGN KEY (DID)
                    REFERENCES document (DID)
                    ON UPDATE CASCADE
                    ON DELETE CASCADE,

                CONSTRAINT fk_title_state
                    FOREIGN KEY (lang)
                    REFERENCES lang (CID)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        print("[DEBUG] Enabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        db.commit()
        print("[OK] Ο πίνακας title δημιουργήθηκε επιτυχώς")

    except Exception as e:
        print("[ERROR] create_title_table FAILED")
        print("[MYSQL ERROR]", e)

        db.rollback()

        import logging
        import traceback
        logging.error(
            "[TITLE_TABLE_CREATE_ERROR]\n%s",
            traceback.format_exc()
        )

        raise


# -------------------------------------------------
# INSERT titles (όλοι οι τίτλοι σε όλες τις γλώσσες)
# -------------------------------------------------
def insert_title(did, root, cursor, db):
    if not did or root is None:
        return

    invention_titles = root.findall(".//invention-title")
    if not invention_titles:
        return

    for title_elem in invention_titles:
        try:
            title_text = "".join(title_elem.itertext()).strip()
            if not title_text:
                continue

            lang_code = title_elem.attrib.get("lang")
            if not lang_code:
                continue

            lang_id = lang_mapping.get(lang_code)
            if lang_id is None:
                logging.error(
                    "[TITLE_LANG_ERROR] DID %s: άγνωστη γλώσσα '%s'",
                    did,
                    lang_code
                )
                continue

            title_chars_count = len(title_text)
            title_words_count = len(title_text.split())

            cursor.execute("""
                INSERT INTO title
                    (DID, title_text, lang, title_chars_count, title_words_count)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                did,
                title_text,
                lang_id,
                title_chars_count,
                title_words_count
            ))

        except Exception:
            logging.error(
                "[TITLE_INSERT_ERROR] DID %s\n%s",
                did,
                traceback.format_exc()
            )

    try:
        db.commit()
    except Exception:
        db.rollback()
        logging.error(
            "[TITLE_COMMIT_ERROR] DID %s\n%s",
            did,
            traceback.format_exc()
        )
