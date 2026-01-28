
import logging
import traceback
import xml.etree.ElementTree as ET
from collections import defaultdict

from lang import lang_mapping
from loadsource import loadsource_mapping

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

# errors.log → DB / logic errors
logging.basicConfig(
    filename="errors.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# bad_files.log → ONLY bad XML files
bad_logger = logging.getLogger("bad_files")
bad_logger.setLevel(logging.ERROR)

bad_handler = logging.FileHandler("bad_files.log", encoding="utf-8")
bad_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(message)s")
)

bad_logger.addHandler(bad_handler)

# --------------------------------------------------
# CREATE TABLE description
# --------------------------------------------------
def create_description_table(cursor, db):
    try:
        print("[DEBUG] create_description_table: START")

        print("[DEBUG] Disabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        print("[DEBUG] Dropping table description if exists")
        cursor.execute("DROP TABLE IF EXISTS description")

        print("[DEBUG] Creating table description")
        cursor.execute("""
            CREATE TABLE description (
                DEID INT UNSIGNED NOT NULL AUTO_INCREMENT,
                DID INT UNSIGNED NOT NULL,

                description_chars_count INT UNSIGNED NOT NULL DEFAULT 0,
                description_pars_count  INT UNSIGNED NOT NULL DEFAULT 0,
                description_words_count INT UNSIGNED NOT NULL DEFAULT 0,

                lang TINYINT UNSIGNED NOT NULL,
                load_source TINYINT UNSIGNED NOT NULL,

                PRIMARY KEY (DEID),
                UNIQUE KEY uq_description (DID, lang, load_source),

                KEY idx_description_DID (DID),
                KEY idx_description_lang (lang),
                KEY idx_description_load_source (load_source),

                CONSTRAINT fk_description_document
                    FOREIGN KEY (DID)
                    REFERENCES document (DID)
                    ON UPDATE CASCADE
                    ON DELETE CASCADE,

                CONSTRAINT fk_description_lang
                    FOREIGN KEY (lang)
                    REFERENCES lang (CID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,

                CONSTRAINT fk_description_load_source
                    FOREIGN KEY (load_source)
                    REFERENCES loadsource (LID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        print("[DEBUG] Enabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        db.commit()
        print("[OK] Ο πίνακας description δημιουργήθηκε επιτυχώς")

    except Exception as e:
        print("[ERROR] create_description_table FAILED")
        print("[MYSQL ERROR]", e)

        db.rollback()

        import logging
        import traceback
        logging.error(
            "[DESCRIPTION_TABLE_CREATE_ERROR]\n%s",
            traceback.format_exc()
        )

        raise


# --------------------------------------------------
# INSERT description (DEFENSIVE & NULL-SAFE)
# --------------------------------------------------

def insert_description(did, root, cursor, db):
    logging.debug("[DESC] insert_description | DID=%s", did)

    if did is None:
        raise ValueError("DID is None")

    if root is None:
        raise ValueError("XML root is None")

    try:
        description_elems = root.findall(".//description")
    except Exception:
        logging.error(
            "[DESCRIPTION_PARSE_ERROR]\n%s",
            traceback.format_exc()
        )
        raise

    if not description_elems:
        return

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

        p_count = len(desc.findall(".//p"))
        pars_by_key[(lang_code, load_source_attr)] += max(1, p_count)

    try:
        for (lang_code, load_source_attr), texts in texts_by_key.items():
            lang_id = lang_mapping.get(lang_code)
            load_source_id = loadsource_mapping.get(load_source_attr)

            if lang_id is None or load_source_id is None:
                logging.warning(
                    "[DESCRIPTION_SKIP] DID=%s lang=%s load_source=%s",
                    did, lang_code, load_source_attr
                )
                continue

            full_text = " ".join(texts)

            # NULL-SAFE NORMALIZATION (covers all edge cases)
            chars_count = len(full_text) if full_text else 0
            words_count = len(full_text.split()) if full_text else 0
            pars_count = pars_by_key.get(
                (lang_code, load_source_attr), 0
            )

            if pars_count <= 0:
                pars_count = 1

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
                chars_count,
                pars_count,
                words_count,
                lang_id,
                load_source_id
            ))

        db.commit()

    except Exception:
        db.rollback()
        logging.error(
            "[DESCRIPTION_INSERT_ERROR] DID=%s\n%s",
            did,
            traceback.format_exc()
        )
        raise

# --------------------------------------------------
# MAIN XML BATCH PROCESSOR
# --------------------------------------------------

def process_xml_files(xml_files, cursor, db):
    """
    xml_files: iterable of (xml_file_path, did)
    """

    for xml_file, did in xml_files:
        try:
            with open(xml_file, "r", encoding="utf-8") as f:
                xml_content = f.read()

            # STRICT XML PARSING
            try:
                root = ET.fromstring(xml_content)
            except Exception as e:
                bad_logger.error(
                    "XML PARSE ERROR | file=%s\n%s\n%s",
                    xml_file,
                    str(e),
                    xml_content
                )
                continue  # ⬅️ ΠΑΕΙ ΣΤΟ ΕΠΟΜΕΝΟ XML

            insert_description(did, root, cursor, db)

        except Exception:
            bad_logger.error(
                "PROCESSING ERROR | file=%s\n%s",
                xml_file,
                traceback.format_exc()
            )
            continue  # ⬅️ ΠΑΕΙ ΣΤΟ ΕΠΟΜΕΝΟ XML
