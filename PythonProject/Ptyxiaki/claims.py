
import logging
import traceback

from lang import lang_mapping
from loadsource import loadsource_mapping


# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# --------------------------------------------------
# CREATE TABLE claims
# --------------------------------------------------
def create_claims_table(cursor, db):
    try:
        print("[DEBUG] create_claims_table: START")

        print("[DEBUG] Disabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        print("[DEBUG] Dropping table claims if exists")
        cursor.execute("DROP TABLE IF EXISTS claims")

        print("[DEBUG] Creating table claims")
        cursor.execute("""
            CREATE TABLE claims (
                CID INT UNSIGNED NOT NULL AUTO_INCREMENT,
                DID INT UNSIGNED NOT NULL,

                claims_chars_count INT UNSIGNED,
                claims_words_count INT UNSIGNED,

                lang TINYINT UNSIGNED,
                load_source TINYINT UNSIGNED,

                PRIMARY KEY (CID),

                KEY idx_claims_DID (DID),
                
                KEY idx_claims_load_source (load_source),

                CONSTRAINT fk_claims_document
                    FOREIGN KEY (DID)
                    REFERENCES document (DID)
                    ON UPDATE CASCADE
                    ON DELETE CASCADE,
                    
                    CONSTRAINT fk_claims_lang
                    FOREIGN KEY (lang)
                    REFERENCES lang (CID)
                    ON UPDATE CASCADE
                    ON DELETE CASCADE,

                CONSTRAINT fk_claims_loadsource
                    FOREIGN KEY (load_source)
                    REFERENCES loadsource (LID)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL
                    
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        print("[DEBUG] Enabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        db.commit()
        print("[OK] Ο πίνακας claims δημιουργήθηκε επιτυχώς")

    except Exception as e:
        print("[ERROR] create_claims_table FAILED")
        print("[MYSQL ERROR]", e)

        db.rollback()

        import logging
        import traceback
        logging.error(
            "[CLAIMS_TABLE_CREATE_ERROR]\n%s",
            traceback.format_exc()
        )

        raise



# --------------------------------------------------
# INSERT claims
# --------------------------------------------------
def insert_claims(did, root, cursor, db):
    logging.error("INSERT CLAIMS – DID=%s", did)

    if not did or root is None:
        return

    claims_elem = root.find(".//claims")
    if claims_elem is None:
        return

    # -------- attributes <claims>
    lang_code = claims_elem.attrib.get("lang")
    load_source_attr = claims_elem.attrib.get("load-source")

    lang_id = lang_mapping.get(lang_code)
    load_source_id = loadsource_mapping.get(load_source_attr)

    # -------- συλλογή ΟΛΟΥ του claim text
    texts = []

    for claim_text in claims_elem.findall(".//claim-text"):
        text = "".join(claim_text.itertext()).strip()
        if text:
            texts.append(text)

    if not texts:
        logging.error("FOUND %d <claim-text> ELEMENTS", len(texts))

        return

    full_text = " ".join(texts)

    claims_chars_count = len(full_text)
    claims_words_count = len(full_text.split())

    try:
        cursor.execute("""
            INSERT INTO claims
                (DID, claims_chars_count, claims_words_count, lang, load_source)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            did,
            claims_chars_count,
            claims_words_count,
            lang_id,
            load_source_id
        ))

        db.commit()

    except Exception:
        db.rollback()
        logging.error(
            "[CLAIMS_INSERT_ERROR] DID %s\n%s",
            did,
            traceback.format_exc()
        )

