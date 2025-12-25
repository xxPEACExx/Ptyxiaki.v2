#
# import traceback
#
# def log_error(message):
#     with open("errors.log", "a", encoding="utf-8") as f:
#         f.write(message + "\n")
#
# def get_lang_id(lang_code, cursor, db):
#     try:
#         cursor.execute("SELECT CID FROM state WHERE country_name = %s", (lang_code,))
#         result = cursor.fetchone()
#         if result:
#             return result[0]
#         else:
#             try:
#                 cursor.execute("INSERT INTO state (country_name) VALUES (%s)", (lang_code,))
#                 db.commit()
#                 return cursor.lastrowid
#             except Exception as insert_err:
#                 log_error(f"[INSERT_ERROR] state insert lang_code: {lang_code}, error: {insert_err}")
#                 db.rollback()
#                 return None
#     except Exception as select_err:
#         log_error(f"[SELECT_ERROR] state select lang_code: {lang_code}, error: {select_err}")
#         return None
#
# def insert_title(did, root, cursor, db):
#     if not did or root is None:
#         return
#
#     invention_titles = root.findall(".//invention-title")
#     title_text = None
#     lang_code = None
#
#     for title in invention_titles:
#         if title.attrib.get('lang') == 'EN':
#             title_text = ''.join(title.itertext()).strip()
#             lang_code = title.attrib.get('lang')
#             break
#
#     if not title_text:
#         return  # Δεν υπάρχει τίτλος στα Αγγλικά
#
#     # Υπολογισμός μεγέθους
#     size_title_chars = len(title_text)
#     size_title_words = len(title_text.split())
#
#     lang_id = get_lang_id(lang_code, cursor, db)
#     if lang_id is None:
#         log_error(f"[ERROR] Δεν βρέθηκε ή δεν εισήχθη το lang_id για γλώσσα: {lang_code}")
#         return
#
#     try:
#         cursor.execute("""
#             INSERT INTO title (did, title_text, lang, size_title_chars, size_title_words)
#             VALUES (%s, %s, %s, %s, %s)
#             ON DUPLICATE KEY UPDATE
#                 title_text = VALUES(title_text),
#                 lang = VALUES(lang),
#                 size_title_chars = VALUES(size_title_chars),
#                 size_title_words = VALUES(size_title_words)
#         """, (did, title_text, lang_id, size_title_chars, size_title_words))
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         log_error(f"[INSERT_ERROR] title insert did: {did}, error: {e}")
#

import logging
import traceback
from state import lang_mapping

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(
    filename='errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_error(message):
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

# -------------------------------------------------
# CREATE TABLE title
# ΜΟΝΟ FK: DID -> document(DID)
# -------------------------------------------------
def create_title_table(cursor, db):
    try:
        cursor.execute("DROP TABLE IF EXISTS title")

        cursor.execute("""
            CREATE TABLE title (
                tID INT NOT NULL AUTO_INCREMENT,
                DID MEDIUMINT UNSIGNED,
                title_text VARCHAR(255),
                lang TINYINT,
                size_title_chars SMALLINT,
                size_title_words TINYINT,

                PRIMARY KEY (tID),

                CONSTRAINT fk_title_document
                    FOREIGN KEY (DID)
                    REFERENCES document(DID)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE

            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("[OK] Ο πίνακας title δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στο create_title_table: %s", e)

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
            title_text = ''.join(title_elem.itertext()).strip()
            if not title_text:
                continue

            lang_code = title_elem.attrib.get("lang")
            if not lang_code:
                continue

            lang_id = lang_mapping.get(lang_code)
            if lang_id is None:
                log_error(f"[TITLE_LANG_ERROR] DID {did}: άγνωστη γλώσσα '{lang_code}'")
                continue

            size_title_chars = len(title_text)
            size_title_words = len(title_text.split())

            cursor.execute("""
                INSERT INTO title
                (DID, title_text, lang, size_title_chars, size_title_words)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                did,
                title_text,
                lang_id,
                size_title_chars,
                size_title_words
            ))

        except Exception:
            log_error(f"[TITLE_PARSE_ERROR] DID {did}:\n{traceback.format_exc()}")

    try:
        db.commit()
    except Exception as commit_err:
        db.rollback()
        log_error(f"[TITLE_COMMIT_ERROR] DID {did}: {commit_err}")
