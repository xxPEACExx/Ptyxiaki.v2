import logging
import traceback
from collections import defaultdict

from state import lang_mapping
from loadsource import loadsource_mapping


# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(
    filename="errors.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



# --------------------------------------------------
# CREATE TABLE description
# --------------------------------------------------
def create_description_table(cursor, db):
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS description")

        cursor.execute("""
            CREATE TABLE description (
                DEID INT NOT NULL AUTO_INCREMENT,
                DID INT UNSIGNED NOT NULL,

                description_chars_count INT,
                description_pars_count INT,
                description_words_count INT,

                lang TINYINT UNSIGNED NOT NULL,
                load_source TINYINT  NOT NULL,

                PRIMARY KEY (DEID),

                UNIQUE KEY uq_description (DID, lang, load_source),

                KEY idx_description_did (DID),
                KEY idx_description_lang (lang),
                KEY idx_description_load_source (load_source),

                CONSTRAINT fk_description_document
                    FOREIGN KEY (DID)
                    REFERENCES document (DID)
                    ON DELETE CASCADE,

                CONSTRAINT fk_description_lang
                    FOREIGN KEY (lang)
                    REFERENCES state (CID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,

                CONSTRAINT fk_description_load_source
                    FOREIGN KEY (load_source)
                    REFERENCES loadsource (LID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db.commit()

        print("[OK] Ο πίνακας description δημιουργήθηκε")


    except Exception as e:

        db.rollback()

        print("CREATE DESCRIPTION TABLE FAILED:")

        print(e)

        logging.error(

            "[DESCRIPTION_TABLE_CREATE_ERROR]\n%s",

            traceback.format_exc()

        )

        raise


# --------------------------------------------------
# INSERT description
# --------------------------------------------------
def insert_description(did, root, cursor, db):
    logging.debug("[DESC] enter insert_description | DID=%s", did)
    if did is None or root is None:
        return

    try:
        description_elems = root.findall(".//description")
    except Exception:
        logging.error(
            "[DESCRIPTION_PARSE_ERROR]\n%s",
            traceback.format_exc()
        )
        return

    if not description_elems:
        return

    # --------------------------------------------------
    # Συλλογή κειμένου & παραγράφων ανά (lang, load_source)
    # --------------------------------------------------
    texts_by_key = defaultdict(list)
    pars_by_key = defaultdict(int)

    for desc in description_elems:
        lang_code = desc.attrib.get("lang")
        load_source_attr = desc.attrib.get("load-source")

        if not lang_code or not load_source_attr:
            continue

        text = "".join(desc.itertext()).strip()
        if not text:
            continue

        texts_by_key[(lang_code, load_source_attr)].append(text)

        # μέτρηση παραγράφων
        p_count = len(desc.findall(".//p"))
        pars_by_key[(lang_code, load_source_attr)] += max(1, p_count)

    # --------------------------------------------------
    # INSERT / UPDATE ανά (lang, load_source)
    # --------------------------------------------------
    try:
        for (lang_code, load_source_attr), texts in texts_by_key.items():
            lang_id = lang_mapping.get(lang_code)
            load_source_id = loadsource_mapping.get(load_source_attr)

            if lang_id is None or load_source_id is None:
                logging.warning(
                    "[DESCRIPTION_SKIP] DID %s | lang=%s | load_source=%s",
                    did, lang_code, load_source_attr
                )
                continue

            full_text = " ".join(texts)

            cursor.execute("""
                INSERT INTO description (
                    DID,
                    description_chars_count,
                    description_pars_count,
                    description_words_count,
                    lang,
                    load_source
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    description_chars_count = VALUES(description_chars_count),
                    description_pars_count  = VALUES(description_pars_count),
                    description_words_count = VALUES(description_words_count)
            """, (
                did,
                len(full_text),
                pars_by_key[(lang_code, load_source_attr)],
                len(full_text.split()),
                lang_id,
                load_source_id
            ))

        db.commit()

    except Exception:
        db.rollback()
        logging.error(
            "[DESCRIPTION_INSERT_ERROR] DID %s\n%s",
            did,
            traceback.format_exc()
        )
        raise
