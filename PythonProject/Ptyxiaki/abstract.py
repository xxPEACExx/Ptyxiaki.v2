from lang import lang_mapping
from loadsource import loadsource_mapping

import logging
import traceback
from collections import defaultdict

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --------------------------------------------------
# CREATE TABLE abstract (ΔΙΟΡΘΩΜΕΝΟ)
# --------------------------------------------------
def create_abstract_table(cursor, db):
    try:
        print("[DEBUG] create_abstract_table: START")

        print("[DEBUG] Disabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        print("[DEBUG] Dropping table abstract if exists")
        cursor.execute("DROP TABLE IF EXISTS abstract")

        print("[DEBUG] Creating table abstract")
        cursor.execute("""
            CREATE TABLE abstract (
                AID INT UNSIGNED NOT NULL AUTO_INCREMENT,
                DID INT UNSIGNED NOT NULL,

                abstract_chars_count INT UNSIGNED NOT NULL,
                abstract_words_count INT UNSIGNED NOT NULL,

                lang TINYINT UNSIGNED NOT NULL,
                load_source TINYINT UNSIGNED NOT NULL,

                PRIMARY KEY (AID),
                UNIQUE KEY uniq_abstract (DID, lang, load_source),

                KEY idx_abstract_DID (DID),
                KEY idx_abstract_lang (lang),
                KEY idx_abstract_load_source (load_source),

                CONSTRAINT fk_abstract_document
                    FOREIGN KEY (DID)
                    REFERENCES document (DID)
                    ON UPDATE CASCADE
                    ON DELETE CASCADE,

                CONSTRAINT fk_abstract_state
                    FOREIGN KEY (lang)
                    REFERENCES lang (CID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,

                CONSTRAINT fk_abstract_loadsource
                    FOREIGN KEY (load_source)
                    REFERENCES loadsource (LID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        print("[DEBUG] Enabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        db.commit()
        print("[OK] Ο πίνακας abstract δημιουργήθηκε επιτυχώς")

    except Exception as e:
        print("[ERROR] create_abstract_table FAILED")
        print("[MYSQL ERROR]", e)

        db.rollback()

        import logging
        import traceback
        logging.error(
            "Σφάλμα στο create_abstract_table:\n%s",
            traceback.format_exc()
        )

        raise



# --------------------------------------------------
# INSERT abstract (FULL DEBUG VERSION)
# --------------------------------------------------



# --------------------------------------------------
# INSERT abstract (CORRECTED & CLEAN)
# --------------------------------------------------
def insert_abstract(did, root, cursor, db):
    if not did or root is None:
        return

    try:
        abstract_elems = root.findall(".//abstract")
    except Exception:
        logging.error("[ABSTRACT_PARSE_ERROR]\n%s", traceback.format_exc())
        return

    if not abstract_elems:
        return

    # --------------------------------------------------
    # συλλογή κειμένου ανά (lang, load_source)
    # --------------------------------------------------
    texts_by_key = defaultdict(list)

    for abstract_elem in abstract_elems:
        lang_code = abstract_elem.attrib.get("lang")
        load_source_attr = abstract_elem.attrib.get("load-source")

        if not lang_code or not load_source_attr:
            continue

        text = "".join(abstract_elem.itertext())
        text = text.encode("utf-8", errors="ignore").decode("utf-8").strip()

        texts_by_key[(lang_code, load_source_attr)].append(text)

    # --------------------------------------------------
    # INSERT ανά (lang, load_source)
    # --------------------------------------------------
    for (lang_code, load_source_attr), texts in texts_by_key.items():

        full_text = " ".join(t for t in texts if t)

        abstract_chars_count = len(full_text)
        abstract_words_count = len(full_text.split())

        lang_id = lang_mapping.get(lang_code)
        load_source_id = loadsource_mapping.get(load_source_attr)

        if lang_id is None or load_source_id is None:
            logging.warning(
                "[ABSTRACT_SKIP] DID %s | lang=%s | load_source=%s",
                did, lang_code, load_source_attr
            )
            continue

        try:
            cursor.execute("""
                INSERT INTO abstract
                    (DID,
                     abstract_chars_count,
                     abstract_words_count,
                     lang,
                     load_source)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                did,
                abstract_chars_count,
                abstract_words_count,
                lang_id,
                load_source_id
            ))

        except Exception:
            db.rollback()
            logging.error(
                "[ABSTRACT_INSERT_ERROR] DID %s | lang=%s | load_source=%s\n%s",
                did,
                lang_code,
                load_source_attr,
                traceback.format_exc()
            )
            return

    # --------------------------------------------------
    # COMMIT ΜΙΑ ΦΟΡΑ
    # --------------------------------------------------
    try:
        db.commit()
    except Exception:
        logging.error("[ABSTRACT_COMMIT_ERROR]\n%s", traceback.format_exc())

