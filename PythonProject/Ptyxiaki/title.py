#
#
# import logging
# import traceback
# from state import lang_mapping
#
# # -------------------------------------------------
# # Logging
# # -------------------------------------------------
# logging.basicConfig(
#     filename='errors.log',
#     level=logging.ERROR,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )
#
# def log_error(message):
#     with open("errors.log", "a", encoding="utf-8") as f:
#         f.write(message + "\n")
#
# # -------------------------------------------------
# # CREATE TABLE title
# # ΜΟΝΟ FK: DID -> document(DID)
# # -------------------------------------------------
# def create_title_table(cursor, db):
#     try:
#         cursor.execute("DROP TABLE IF EXISTS title")
#
#         cursor.execute("""
#             CREATE TABLE title (
#                 tID INT NOT NULL AUTO_INCREMENT,
#                 DID INT UNSIGNED,
#                 title_text VARCHAR(255),
#                 lang TINYINT,
#                 title_chars_count SMALLINT,
#                 title_words_count TINYINT,
#
#                 PRIMARY KEY (tID),
#
#                 CONSTRAINT fk_title_document
#                     FOREIGN KEY (DID)
#                     REFERENCES document(DID)
#                     ON DELETE CASCADE
#                     ON UPDATE CASCADE
#
#             ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
#         """)
#
#         db.commit()
#         print("[OK] Ο πίνακας title δημιουργήθηκε")
#
#     except Exception as e:
#         db.rollback()
#         logging.error("Σφάλμα στο create_title_table: %s", e)
#
# # -------------------------------------------------
# # INSERT titles (όλοι οι τίτλοι σε όλες τις γλώσσες)
# # -------------------------------------------------
# def insert_title(did, root, cursor, db):
#     if not did or root is None:
#         return
#
#     invention_titles = root.findall(".//invention-title")
#     if not invention_titles:
#         return
#
#     for title_elem in invention_titles:
#         try:
#             title_text = ''.join(title_elem.itertext()).strip()
#             if not title_text:
#                 continue
#
#             lang_code = title_elem.attrib.get("lang")
#             if not lang_code:
#                 continue
#
#             lang_id = lang_mapping.get(lang_code)
#             if lang_id is None:
#                 log_error(f"[TITLE_LANG_ERROR] DID {did}: άγνωστη γλώσσα '{lang_code}'")
#                 continue
#
#             size_title_chars = len(title_text)
#             size_title_words = len(title_text.split())
#
#             cursor.execute("""
#                 INSERT INTO title
#                 (DID, title_text, lang, size_title_chars, size_title_words)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (
#                 did,
#                 title_text,
#                 lang_id,
#                 size_title_chars,
#                 size_title_words
#             ))
#
#         except Exception:
#             log_error(f"[TITLE_PARSE_ERROR] DID {did}:\n{traceback.format_exc()}")
#
#     try:
#         db.commit()
#     except Exception as commit_err:
#         db.rollback()
#         log_error(f"[TITLE_COMMIT_ERROR] DID {did}: {commit_err}")

import logging
import traceback
from state import lang_mapping


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
        cursor.execute("DROP TABLE IF EXISTS title")

        cursor.execute("""
            CREATE TABLE title (
                tID INT NOT NULL AUTO_INCREMENT,
                DID INT UNSIGNED NOT NULL,

                title_text VARCHAR(255),
                lang TINYINT,

                title_chars_count SMALLINT,
                title_words_count SMALLINT,

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

    except Exception:
        db.rollback()
        logging.error(
            "[TITLE_TABLE_CREATE_ERROR]\n%s",
            traceback.format_exc()
        )


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
