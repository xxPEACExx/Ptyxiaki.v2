
from state import lang_mapping
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
# CREATE TABLE abstract
# --------------------------------------------------
import logging
#
# def create_abstract_table(cursor, db):
#     try:
#         cursor.execute("""
#             DROP TABLE IF EXISTS abstract
#         """)
#
#         cursor.execute("""
#             CREATE TABLE abstract (
#                 AID INT NOT NULL AUTO_INCREMENT,
#                 DID MEDIUMINT UNSIGNED NOT NULL,
#                 abstract_size_chars int UNSIGNED NOT NULL,
#                 abstract_word_count int UNSIGNED NOT NULL,
#                 lang tinyint unsigned NOT NULL,
#                 load_source TINYINT NOT NULL,
#
#                 PRIMARY KEY (AID),
#
#                 KEY idx_abstract_DID (DID),
#                 KEY idx_abstract_lang (lang),
#                 KEY idx_abstract_load_source (load_source),
#
#                 CONSTRAINT fk_abstract_document
#                     FOREIGN KEY (DID) REFERENCES document (did)
#                     ON UPDATE CASCADE
#                     ON DELETE RESTRICT,
#
#                 CONSTRAINT fk_abstract_state
#                     FOREIGN KEY (lang) REFERENCES state (CID)
#                     ON UPDATE CASCADE
#                     ON DELETE RESTRICT,
#
#                 CONSTRAINT fk_abstract_loadsource
#                     FOREIGN KEY (load_source) REFERENCES loadsource (LID)
#                     ON UPDATE CASCADE
#                     ON DELETE RESTRICT
#             ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
#         """)
#
#         db.commit()
#         print("[OK] Ο πίνακας abstract δημιουργήθηκε")
#
#
#     except Exception as e:
#
#         db.rollback()
#
#         print("MYSQL ERROR:", e)
#
#         logging.error("Σφάλμα στο create_abstract_table: %s", e)

from state import lang_mapping
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
        print("[DEBUG] Dropping table abstract")

        cursor.execute("DROP TABLE IF EXISTS abstract")

        print("[DEBUG] Creating table abstract")

        cursor.execute("""
            CREATE TABLE abstract (
                AID INT NOT NULL AUTO_INCREMENT,
                DID MEDIUMINT UNSIGNED NOT NULL,

                abstract_size_chars INT UNSIGNED NOT NULL,
                abstract_word_count INT UNSIGNED NOT NULL,

                lang TINYINT UNSIGNED NOT NULL,
                load_source TINYINT NOT NULL,

                PRIMARY KEY (AID),
                UNIQUE KEY uniq_abstract (DID, lang, load_source),

                KEY idx_abstract_DID (DID),
                KEY idx_abstract_lang (lang),
                KEY idx_abstract_load_source (load_source),

                CONSTRAINT fk_abstract_document
                    FOREIGN KEY (DID) REFERENCES document (did)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,

                CONSTRAINT fk_abstract_state
                    FOREIGN KEY (lang) REFERENCES state (CID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,

                CONSTRAINT fk_abstract_loadsource
                    FOREIGN KEY (load_source) REFERENCES loadsource (LID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("[OK] Ο πίνακας abstract δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        print("[MYSQL ERROR][CREATE ABSTRACT]", e)
        logging.error("Σφάλμα στο create_abstract_table:\n%s", traceback.format_exc())


# --------------------------------------------------
# INSERT abstract (FULL DEBUG VERSION)
# --------------------------------------------------
def insert_abstract(did, root, cursor, db):
    print("\n[DEBUG] ===== insert_abstract START =====")
    print("[DEBUG] DID:", did)

    if not did:
        print("[DEBUG] DID is empty -> RETURN")
        return

    if root is None:
        print("[DEBUG] root is None -> RETURN")
        return

    try:
        abstract_elems = root.findall(".//abstract")
        print("[DEBUG] abstracts found:", len(abstract_elems))
    except Exception as e:
        print("[FATAL] root.findall failed:", e)
        return

    if not abstract_elems:
        print("[DEBUG] No abstracts -> RETURN")
        return

    # --------------------------------------------------
    # Collect text ανά (lang, load_source)
    # --------------------------------------------------
    texts_by_key = defaultdict(list)

    for i, abstract_elem in enumerate(abstract_elems):
        try:
            print(f"[DEBUG] Processing abstract #{i}")

            print("[DEBUG] attribs:", abstract_elem.attrib)

            lang_code = abstract_elem.attrib.get("lang")
            load_source_attr = abstract_elem.attrib.get("load-source")

            if not lang_code or not load_source_attr:
                print("[DEBUG] Missing lang/load-source -> SKIP")
                continue

            text = "".join(abstract_elem.itertext())
            text = text.encode("utf-8", errors="ignore").decode("utf-8")
            text = text.strip()

            print(
                "[DEBUG] text length:",
                len(text),
                "| lang:",
                lang_code,
                "| load:",
                load_source_attr
            )

            texts_by_key[(lang_code, load_source_attr)].append(text)

        except Exception as e:
            print("[ERROR] Abstract loop exception:", e)
            logging.error(
                "[ABSTRACT_PARSE_ERROR]\n%s",
                traceback.format_exc()
            )

    # --------------------------------------------------
    # INSERT ανά (lang, load_source)
    # --------------------------------------------------
    for (lang_code, load_source_attr), texts in texts_by_key.items():
        print(
            "\n[DEBUG] INSERT group:",
            "lang=", lang_code,
            "| load=", load_source_attr,
            "| parts=", len(texts)
        )

        full_text = " ".join(t for t in texts if t)

        abstract_size_chars = len(full_text)
        abstract_word_count = len(full_text.split())

        print(
            "[DEBUG] FINAL COUNTS:",
            "chars=", abstract_size_chars,
            "words=", abstract_word_count
        )

        # ---- mapping
        lang_id = lang_mapping.get(lang_code)
        load_source_id = loadsource_mapping.get(load_source_attr)

        print(
            "[DEBUG] IDs:",
            "lang_id=", lang_id,
            "load_source_id=", load_source_id
        )

        if lang_id is None or load_source_id is None:
            print("[DEBUG] Mapping missing -> SKIP INSERT")
            logging.warning(
                "[ABSTRACT_SKIP] DID %s | lang=%s | load_source=%s",
                did, lang_code, load_source_attr
            )
            continue

        try:
            cursor.execute("""
                INSERT INTO abstract
                    (DID,
                     abstract_size_chars,
                     abstract_word_count,
                     lang,
                     load_source)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                did,
                abstract_size_chars,
                abstract_word_count,
                lang_id,
                load_source_id
            ))

            print("[DEBUG] INSERT OK")

        except Exception as e:
            print("[MYSQL ERROR][INSERT ABSTRACT]", e)
            db.rollback()
            logging.error(
                "[ABSTRACT_INSERT_ERROR]\n%s",
                traceback.format_exc()
            )

    # --------------------------------------------------
    # COMMIT (ΜΟΝΟ ΕΝΑ)
    # --------------------------------------------------
    try:
        db.commit()
        print("[DEBUG] COMMIT OK")
    except Exception as e:
        print("[MYSQL ERROR][COMMIT]", e)

    print("[DEBUG] ===== insert_abstract END =====\n")






def insert_abstract(did, root, cursor, db):
    if not did or root is None:
        return

    abstract_elems = root.findall(".//abstract")
    if not abstract_elems:
        return

    # -------- συλλογή κειμένου ανά (lang, load_source)
    texts_by_key = defaultdict(list)

    for abstract_elem in abstract_elems:
        lang_code = abstract_elem.attrib.get("lang")
        load_source_attr = abstract_elem.attrib.get("load-source")

        if not lang_code or not load_source_attr:
            continue

        key = (lang_code, load_source_attr)

        text = "".join(abstract_elem.itertext()).strip()
        texts_by_key[key].append(text or "")

    # -------- insert ανά (lang, load_source)
    for (lang_code, load_source_attr), texts in texts_by_key.items():

        full_text = " ".join(t for t in texts if t)

        if full_text:
            abstract_size_chars = len(full_text)
            abstract_word_count = len(full_text.split())
        else:
            abstract_size_chars = 0
            abstract_word_count = 0

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
                     abstract_size_chars,
                     abstract_word_count,
                     lang,
                     load_source)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                did,
                abstract_size_chars,
                abstract_word_count,
                lang_id,
                load_source_id
            ))

            db.commit()

        except Exception:
            db.rollback()
            logging.error(
                "[ABSTRACT_INSERT_ERROR] DID %s | lang=%s | load_source=%s\n%s",
                did,
                lang_code,
                load_source_attr,
                traceback.format_exc()
            )

